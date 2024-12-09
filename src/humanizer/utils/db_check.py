# src/humanizer/utils/db_check.py
import asyncio
import asyncpg
from humanizer.utils.logging import get_logger

logger = get_logger(__name__)

async def check_postgres_connection(
    host: str = "localhost",
    port: int = 5432,
    user: str = "postgres",
    password: str = "postgres",
    database: str = "humanizer"
) -> bool:
    """Check PostgreSQL connection and create database if needed."""
    try:
        conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        conn = await asyncpg.connect(conn_str)
        await conn.close()
        logger.info(f"Successfully connected to database '{database}'")
        return True
    except asyncpg.InvalidCatalogNameError:
        logger.info(f"Database '{database}' not found, attempting to create...")
        system_conn_str = f"postgresql://{user}:{password}@{host}:{port}/postgres"
        try:
            conn = await asyncpg.connect(system_conn_str)
            await conn.execute(f'CREATE DATABASE {database}')
            await conn.close()
            logger.info(f"Successfully created database '{database}'")
            return True
        except Exception as e:
            logger.error(f"Failed to create database: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"PostgreSQL connection check failed: {str(e)}")
        return False

async def check_pgvector_extension(
    host: str = "localhost",
    port: int = 5432,
    user: str = "postgres",
    password: str = "postgres",
    database: str = "humanizer"
) -> bool:
    """Check if pgvector extension is available and install if needed."""
    conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    try:
        conn = await asyncpg.connect(conn_str)

        # First check if pgvector is available
        result = await conn.fetch("""
            SELECT EXISTS (
                SELECT 1
                FROM pg_available_extensions
                WHERE name = 'vector'
            );
        """)

        if not result[0]['exists']:
            logger.error("pgvector extension is not available in PostgreSQL")
            logger.error("Please install pgvector using: brew install pgvector")
            await conn.close()
            return False

        # Try to create extension
        try:
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector;')
            logger.info("pgvector extension enabled successfully")
            await conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to create pgvector extension: {e}")
            await conn.close()
            return False

    except Exception as e:
        logger.error(f"pgvector extension check failed: {e}")
        return False

__all__ = ['check_postgres_connection', 'check_pgvector_extension']

# Simple command-line interface
if __name__ == "__main__":
    async def main():
        # Check PostgreSQL
        if await check_postgres_connection():
            print("PostgreSQL connection successful")
        else:
            print("PostgreSQL connection failed")
            return

        # Check pgvector
        if await check_pgvector_extension():
            print("pgvector extension check successful")
        else:
            print("pgvector extension check failed")

    asyncio.run(main())
