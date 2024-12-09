# src/humanizer/scripts/verify_config.py
from humanizer.config import get_settings
from humanizer.utils.db_check import check_postgres_connection, check_pgvector_extension
import asyncio

async def verify_setup():
    settings = get_settings()

    # Check database connection
    db_ok = await check_postgres_connection()
    print(f"Database connection: {'OK' if db_ok else 'FAILED'}")

    # Check pgvector
    vector_ok = await check_pgvector_extension()
    print(f"pgvector extension: {'OK' if vector_ok else 'FAILED'}")

    # Test settings
    print("\nConfiguration:")
    print(f"Database URL: {settings.database_url}")
    print(f"Ollama URL: {settings.ollama_base_url}")
    print(f"Embedding Model: {settings.embedding_model}")

if __name__ == "__main__":
    asyncio.run(verify_setup())
