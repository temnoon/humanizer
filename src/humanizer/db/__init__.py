# src/humanizer/db/__init__.py
from humanizer.utils.db_check import check_postgres_connection, check_pgvector_extension
from humanizer.utils.logging import get_logger

logger = get_logger(__name__)

async def ensure_database() -> None:
    """Ensure database exists with required extensions"""
    try:
        if not await check_postgres_connection():
            raise RuntimeError("Failed to establish PostgreSQL connection")

        if not await check_pgvector_extension():
            raise RuntimeError("Failed to verify pgvector extension")

        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

__all__ = ['ensure_database']
