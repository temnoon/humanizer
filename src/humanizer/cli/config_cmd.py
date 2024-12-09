# src/humanizer/cli/config_cmd.py
import click
from pathlib import Path
import json
import os
from humanizer.config import get_settings
from humanizer.utils.logging import get_logger

logger = get_logger(__name__)

@click.group()
def config():
    """Manage configuration settings"""
    pass

@config.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text')
def show(format):
    """Show current configuration"""
    settings = get_settings()
    if format == 'json':
        click.echo(json.dumps(settings.dict(), indent=2))
    else:
        for key, value in settings.dict().items():
            click.echo(f"{key}: {value}")

@config.command()
@click.argument('key')
@click.argument('value')
def set(key: str, value: str):
    """Set configuration value"""
    settings = get_settings()
    if hasattr(settings, key):
        setattr(settings, key, value)
        click.echo(f"Updated {key} = {value}")
    else:
        click.echo(f"Unknown configuration key: {key}", err=True)

@config.command()
def verify():
    """Verify configuration"""
    from humanizer.utils.db_check import check_postgres_connection
    import asyncio

    async def run_checks():
        # Check database connection
        if await check_postgres_connection():
            click.echo("✓ Database connection OK")
        else:
            click.echo("✗ Database connection FAILED")

        # Check configuration file
        settings = get_settings()
        if Path(settings.config_path).exists():
            click.echo("✓ Configuration file found")
        else:
            click.echo("✗ Configuration file not found")

    asyncio.run(run_checks())

@config.command()
def debug():
    """Show detailed configuration information"""
    settings = get_settings()

    # Check .env file
    env_path = Path(".env")
    if env_path.exists():
        click.echo(f"\nFound .env file at: {env_path.absolute()}")
        # Print first few lines (excluding sensitive info)
        with open(env_path) as f:
            lines = [line.strip() for line in f if line.strip() and not any(
                secret in line.upper() for secret in ['PASSWORD', 'KEY', 'SECRET']
            )]
            click.echo("Environment file preview:")
            for line in lines[:5]:
                click.echo(f"  {line}")
    else:
        click.echo("\nWarning: No .env file found in current directory")

    click.echo("\nEmbedding Configuration:")
    click.echo(f"Model: {settings.embedding_model}")
    click.echo(f"Dimensions: {settings.embedding_dimensions}")
    click.echo(f"Ollama URL: {settings.ollama_base_url}")

    # Verify environment variables
    click.echo("\nEnvironment Variables:")
    env_vars = ['EMBEDDING_MODEL', 'EMBEDDING_DIMENSIONS', 'OLLAMA_BASE_URL']
    for var in env_vars:
        value = os.getenv(var)
        click.echo(f"{var}: {value if value is not None else 'Not set'}")
