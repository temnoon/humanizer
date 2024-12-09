# src/humanizer/cli/project_cmd.py
import click
import asyncio
from pathlib import Path

from sqlalchemy import func, select
from humanizer.utils.project_manager import ProjectManager, ChangeType
from humanizer.utils.logging import get_logger
from humanizer.db.session import get_session
from humanizer.db.models import Content, Message

logger = get_logger(__name__)

@click.group()
def project():
    """Project management commands"""
    pass

@project.command()
@click.argument('change_type', type=click.Choice([ct.value for ct in ChangeType]))
def plan_updates(change_type: str):
    """Generate update plan for specified change type"""
    project_root = Path(__file__).parent.parent.parent.parent
    manager = ProjectManager(project_root)
    plan = manager.generate_update_plan(ChangeType(change_type))

    if not plan:
        click.echo("No files need updating")
        return

    click.echo(f"\nFiles to update for {change_type} changes:")
    for i, file in enumerate(plan, 1):
        click.echo(f"{i}. {file}")

@project.command()
def verify():
    """Verify project structure and dependencies"""
    project_root = Path(__file__).parent.parent.parent.parent
    manager = ProjectManager(project_root)

    # Check dependencies
    issues = manager.verify_dependencies()
    if issues:
        click.echo("Issues found:")
        for issue in issues:
            click.echo(f"  ✗ {issue}")
    else:
        click.echo("✓ All dependencies verified")

    # Check required files
    required_files = [
        "pyproject.toml",
        "src/humanizer/__init__.py",
        "src/humanizer/cli/__init__.py",
    ]

    for file in required_files:
        path = project_root / file
        if path.exists():
            click.echo(f"✓ Found {file}")
        else:
            click.echo(f"✗ Missing {file}")

@project.command()
def status():
    """Show project status summary"""
    async def run():
        async with get_session() as session:
            # Get conversation count
            conv_count = await session.scalar(
                select(func.count()).select_from(Content)
            ) or 0

            # Get message count
            msg_count = await session.scalar(
                select(func.count()).select_from(Message)
            ) or 0

            # Get embedding status
            embedded = await session.scalar(
                select(func.count())
                .select_from(Message)
                .where(Message.embedding.isnot(None))
            ) or 0

            click.echo("\nProject Status")
            click.echo("=" * 40)
            click.echo(f"Conversations: {conv_count:,}")
            click.echo(f"Total Messages: {msg_count:,}")
            click.echo(f"Embedded Messages: {embedded:,}")
            if msg_count > 0:
                click.echo(f"Embedding Progress: {embedded/msg_count*100:.1f}%")
            else:
                click.echo("Embedding Progress: N/A (no messages)")

    asyncio.run(run())

if __name__ == '__main__':
    project()
