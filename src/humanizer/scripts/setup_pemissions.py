# src/humanizer/scripts/setup_permissions.py
import asyncio
import click
from humanizer.utils.logging import get_logger
import asyncpg
import os
from cryptography.fernet import Fernet

logger = get_logger(__name__)

def get_encrypted_password():
    """Get encrypted password from environment variable"""
    key = os.environ.get('POSTGRES_KEY')
    if not key:
        raise ValueError("POSTGRES_KEY environment variable not set")

    encrypted_password = os.environ.get('POSTGRES_PASSWORD_ENCRYPTED')
    if not encrypted_password:
        raise ValueError("POSTGRES_PASSWORD_ENCRYPTED environment variable not set")

    f = Fernet(key)
    return f.decrypt(encrypted_password.encode()).decode()

async def setup_permissions(
    user: str = "postgres",
    database: str = "humanizer"
):
    """Set up database permissions"""
    try:
        # Get password from encrypted env var
        password = get_encrypted_password()

        # Connect as superuser
        conn = await asyncpg.connect(
            user=user,
            password=password,
            database=database
        )

        # Grant permissions
        await conn.execute(f"""
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {user};
            GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {user};
            GRANT ALL PRIVILEGES ON SCHEMA public TO {user};

            ALTER DEFAULT PRIVILEGES IN SCHEMA public
                GRANT ALL ON TABLES TO {user};
            ALTER DEFAULT PRIVILEGES IN SCHEMA public
                GRANT ALL ON SEQUENCES TO {user};
        """)

        logger.info(f"Successfully granted permissions to user {user}")
        await conn.close()

    except Exception as e:
        logger.error(f"Failed to set up permissions: {e}")
        raise

@click.command()
@click.option('--user', default='postgres', help='Database user')
@click.option('--database', default='humanizer',
              help='Database name')
def main(user: str, database: str):
    """Set up database permissions"""
    asyncio.run(setup_permissions(user, database))

if __name__ == '__main__':
    main()
