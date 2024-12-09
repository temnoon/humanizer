# src/humanizer/cli/import_cmd.py
import asyncio
import click
from pathlib import Path
from humanizer.core.content.importer import ConversationImporter
from humanizer.db import ensure_database
from humanizer.utils.logging import get_logger

logger = get_logger(__name__)

@click.command(name='import')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--verbose', is_flag=True, help='Show detailed import information')
@click.option('--batch-size', default=100, help='Number of conversations per batch')
def import_conversations(file_path: str, verbose: bool, batch_size: int):
    """Import conversations from OpenAI archive"""
    async def run():
        try:
            # Ensure database is ready
            await ensure_database()

            # Import conversations
            importer = ConversationImporter()
            imported_ids = await importer.import_file(Path(file_path))

            if verbose:
                click.echo(f"\nImported {len(imported_ids)} conversations:")
                for conv_id in imported_ids:
                    click.echo(f"  - {conv_id}")
            else:
                click.echo(f"Successfully imported {len(imported_ids)} conversations")

        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            raise

    asyncio.run(run())

if __name__ == '__main__':
    import_conversations()
