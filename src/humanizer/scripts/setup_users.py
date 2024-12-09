# src/humanizer/scripts/setup_users.py
import asyncio
import click
from humanizer.utils.logging import get_logger
import asyncpg

logger = get_logger(__name__)

async def create_users(admin_password: str, app_password: str, readonly_password: str):
    """Create database users and roles"""
    # Connect as postgres superuser
    conn = await asyncpg.connect(
        user='postgres',
        database='postgres'
    )

    try:
        # Create roles
        await conn.execute("""
            CREATE ROLE humanizer_read;
            CREATE ROLE humanizer_write;
            CREATE ROLE humanizer_admin_role;
        """)

        # Create users
        await conn.execute(f"""
            CREATE USER humanizer_admin WITH PASSWORD '{admin_password}';
            CREATE USER humanizer_app WITH PASSWORD '{app_password}';
            CREATE USER humanizer_readonly WITH PASSWORD '{readonly_password}';
        """)

        # Grant roles
        await conn.execute("""
            GRANT humanizer_read TO humanizer_write;
            GRANT humanizer_write TO humanizer_admin_role;
            GRANT humanizer_admin_role TO humanizer_admin;
            GRANT humanizer_write TO humanizer_app;
            GRANT humanizer_read TO humanizer_readonly;
        """)

        logger.info("Database users created successfully")
    except Exception as e:
        logger.error(f"Failed to create users: {e}")
        raise
    finally:
        await conn.close()

@click.command()
@click.option('--admin-pass', prompt=True, hide_input=True,
              help='Password for admin user')
@click.option('--app-pass', prompt=True, hide_input=True,
              help='Password for application user')
@click.option('--readonly-pass', prompt=True, hide_input=True,
              help='Password for readonly user')
def setup_users(admin_pass: str, app_pass: str, readonly_pass: str):
    """Set up database users"""
    asyncio.run(create_users(admin_pass, app_pass, readonly_pass))

if __name__ == '__main__':
    setup_users()
