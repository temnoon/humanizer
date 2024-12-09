# src/humanizer/cli/main.py
import click
from typing import Optional
from humanizer.cli.import_cmd import import_conversations
from humanizer.cli.embedding_cmd import embeddings
from humanizer.cli.db_cmd import db
from humanizer.cli.list_cmd import list_cmd
from humanizer.cli.config_cmd import config
from humanizer.cli.search_cmd import search
from humanizer.cli.project_cmd import project
from humanizer.utils.logging import get_logger
from humanizer.cli.types import ClickGroup, ClickHandler
from humanizer.config import load_config

logger = get_logger(__name__)

@click.group()
@click.version_option()
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.option('--config-file', type=click.Path(), help='Custom config file path')
def cli(verbose: bool, config_file: Optional[str] = None) -> None:
    """Humanizer CLI tool for managing conversations and embeddings"""
    if verbose:
        logger.setLevel('DEBUG')
    if config_file:
        load_config(config_file)

# Add commands
cli.add_command(import_conversations)
cli.add_command(embeddings)
cli.add_command(db)
cli.add_command(list_cmd)
cli.add_command(config)
cli.add_command(search)
cli.add_command(project)

if __name__ == '__main__':
    cli()
