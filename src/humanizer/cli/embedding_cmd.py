# src/humanizer/cli/embedding_cmd.py
import asyncio
import click
from typing import Optional
from humanizer.core.content.processor import ContentProcessor
from humanizer.core.embedding.service import EmbeddingService
from humanizer.config import get_settings
from humanizer.db.session import get_session
from humanizer.utils.logging import get_logger
from sqlalchemy import text

logger = get_logger(__name__)

@click.group()
def embeddings() -> None:
    """Manage message embeddings"""
    pass

@embeddings.command()
@click.option('--batch-size', default=50, help='Batch size for processing')
@click.option('--force', is_flag=True, help='Force update of existing embeddings')
@click.option('--model', help='Override default embedding model')
def update(batch_size: int, force: bool, model: Optional[str] = None) -> None:
    """Update embeddings for messages"""
    async def run_update() -> None:
        processor = ContentProcessor()
        if model:
            processor.embedding_service.embedding_model = model

        total = await processor.count_pending_embeddings(force=force)
        if total == 0:
            click.echo("No messages need embedding updates")
            return

        with click.progressbar(length=total, label='Updating embeddings') as bar:
            async for processed in processor.update_embeddings(
                batch_size=batch_size,
                force=force
            ):
                bar.update(processed)

    asyncio.run(run_update())

@embeddings.command()
def status():
    """Show embedding status"""
    async def run():
        processor = ContentProcessor()
        stats = await processor.get_embedding_stats()

        click.echo("\nEmbedding Status")
        click.echo("=" * 40)
        click.echo(f"Total Messages: {stats['total']:,}")
        click.echo(f"With Embeddings: {stats['embedded']:,}")
        click.echo(f"Pending: {stats['pending']:,}")
        if stats['total'] > 0:
            click.echo(f"Progress: {stats['embedded']/stats['total']*100:.1f}%")
        click.echo(f"\nCurrent Model: {processor.embedding_service.embedding_model}")

    asyncio.run(run())

@embeddings.command()
def setup():
    """Verify and setup embedding configuration"""
    async def run():
        settings = get_settings()
        service = EmbeddingService()

        click.echo("\nEmbedding Configuration:")
        click.echo(f"Model: {settings.embedding_model}")
        click.echo(f"Dimensions: {settings.embedding_dimensions}")
        click.echo(f"Ollama URL: {settings.ollama_base_url}")

        # Test embedding creation
        try:
            test_text = "This is a test document"
            embedding = await service.create_embedding(test_text)
            click.echo(f"\nSuccess! Created embedding with {len(embedding)} dimensions")
            click.echo(f"First few values: {embedding[:5]}")

            # Verify database setup
            async with get_session() as session:
                # Check if vector normalization is set up
                result = await session.execute(text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_trigger
                        WHERE tgname = 'normalize_embedding'
                    );
                """))
                has_trigger = result.scalar()

                if has_trigger:
                    click.echo("\n✓ Vector normalization trigger is set up")
                else:
                    click.echo("\n⚠ Vector normalization trigger is missing")
                    click.echo("Run 'humanizer db migrate' to set up triggers")

        except Exception as e:
            click.echo(f"\nError: {str(e)}")

    asyncio.run(run())

@embeddings.command()
def verify_model() -> None:
    """Verify embedding model configuration"""
    async def run():
        settings = get_settings()
        service = EmbeddingService()

        click.echo("Current Configuration:")
        click.echo(f"Model: {settings.embedding_model}")
        click.echo(f"Expected Dimensions: {settings.embedding_dimensions}")

        try:
            # Test with a simple string
            embedding = await service.create_embedding("test")
            click.echo(f"Actual Dimensions: {len(embedding)}")
            click.echo("✓ Model verification successful")
        except Exception as e:
            click.echo(f"✗ Model verification failed: {e}")

    asyncio.run(run())

@embeddings.command()
def test():
    """Test embedding creation with sample text"""
    async def run():
        settings = get_settings()
        test_text = "The sky is blue because of Rayleigh scattering"

        click.echo("\nTesting embedding creation:")
        click.echo(f"Model: {settings.embedding_model}")
        click.echo(f"Test text: {test_text}")

        try:
            service = EmbeddingService()
            embedding = await service.create_embedding(test_text)

            click.echo(f"\nSuccess! Generated embedding with {len(embedding)} dimensions")
            click.echo(f"First few values: {embedding[:5]}")

        except Exception as e:
            click.echo(f"Error: {str(e)}")

    asyncio.run(run())
