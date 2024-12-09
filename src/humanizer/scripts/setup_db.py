# src/humanizer/scripts/setup_db.py
import asyncio
import click
from humanizer.utils.logging import get_logger
from humanizer.utils.db_check import check_postgres_connection
from humanizer.db import ensure_database

logger = get_logger(__name__)

@click.command()
@click.option('--force', is_flag=True, help='Force recreation of database')
def setup_database(force: bool):
    """Set up the Humanizer database"""
    async def run():
        try:
            # Check connection
            if not await check_postgres_connection():
                logger.error("Could not connect to PostgreSQL")
                return

            # Initialize database
            await ensure_database()
            logger.info("Database setup completed successfully")

        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise

    asyncio.run(run())

if __name__ == '__main__':
    setup_database()
