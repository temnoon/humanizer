# src/humanizer/scripts/manage_project.py
import click
from pathlib import Path
from humanizer.utils.project_manager import ProjectManager, ChangeType
from humanizer.utils.logging import get_logger

logger = get_logger(__name__)

@click.group()
def cli():
    """Project management commands"""
    pass

@cli.command()
@click.argument('change_type', type=click.Choice([ct.value for ct in ChangeType]))
def plan_updates(change_type: str):
    """Generate update plan for specified change type"""
    project_root = Path(__file__).parent.parent.parent.parent
    manager = ProjectManager(project_root)

    # Verify dependencies
    if issues := manager.verify_dependencies():
        logger.warning("Dependency issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")

    # Generate plan
    plan = manager.generate_update_plan(ChangeType(change_type))

    click.echo(f"\nFiles to update for {change_type} changes:")
    for i, file in enumerate(plan, 1):
        click.echo(f"{i}. {file}")

if __name__ == '__main__':
    cli()
