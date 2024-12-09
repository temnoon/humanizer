# src/humanizer/db/setup.py
from humanizer.utils.logging import get_logger
from humanizer.config import get_settings

logger = get_logger(__name__)

async def setup_database_users(
    admin_password: str,
    app_password: str,
    readonly_password: str
):
    """Set up database users and permissions"""
    from asyncpg import connect
    settings = get_settings()

    try:
        conn = await connect(
            host=settings.database_url,
            user='postgres'
        )

        # Create roles and users
        await conn.execute(f"""
            CREATE ROLE humanizer_admin LOGIN PASSWORD '{admin_password}';
            CREATE ROLE humanizer_app LOGIN PASSWORD '{app_password}';
            CREATE ROLE humanizer_readonly LOGIN PASSWORD '{readonly_password}';
        """)

        # Grant permissions
        await conn.execute("""
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO humanizer_admin;
            GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO humanizer_app;
            GRANT SELECT ON ALL TABLES IN SCHEMA public TO humanizer_readonly;
        """)

        await conn.close()
        logger.info("Database users and permissions set up successfully")

    except Exception as e:
        logger.error(f"Failed to set up database users: {e}")
        raise
