# src/humanizer/cli/db_cmd.py
import click
import asyncio
from sqlalchemy import text
from humanizer.db import ensure_database
from humanizer.db.session import init_db, get_session
from humanizer.utils.logging import get_logger

logger = get_logger(__name__)

@click.group(name='db')
def db() -> None:
    """Database management commands"""
    pass

@db.command()
@click.option('--force', is_flag=True, help='Force recreation of database')
def init(force: bool) -> None:
    """Initialize database"""
    async def run() -> None:
        # First ensure database exists
        await ensure_database()
        # Then initialize schema
        await init_db(force=force)
        logger.info("Database initialization completed")

    asyncio.run(run())

@db.command()
@click.option('--admin-pass', prompt=True, hide_input=True,
              help='Admin password')
@click.option('--app-pass', prompt=True, hide_input=True,
              help='App password')
@click.option('--readonly-pass', prompt=True, hide_input=True,
              help='Readonly password')
def setup(admin_pass: str, app_pass: str, readonly_pass: str) -> None:
    """Set up database users and permissions"""
    from humanizer.db.setup import setup_database_users
    async def run() -> None:
        await setup_database_users(
            admin_password=admin_pass,
            app_password=app_pass,
            readonly_password=readonly_pass
        )
    asyncio.run(run())

@db.command()
def verify() -> None:
    """Verify database connection and setup"""
    from humanizer.utils.db_check import check_postgres_connection, check_pgvector_extension
    async def run() -> None:
        if await check_postgres_connection():
            click.echo("Database connection: OK")
        else:
            click.echo("Database connection: FAILED")
            return
        if await check_pgvector_extension():
            click.echo("pgvector extension: OK")
        else:
            click.echo("pgvector extension: FAILED")
    asyncio.run(run())

@db.command()
def migrate():
    """Run database migrations"""
    async def run():
        async with get_session() as session:
            # Create the function first
            await session.execute(text("""
                CREATE OR REPLACE FUNCTION normalize_vector()
                RETURNS trigger AS $$
                BEGIN
                    IF NEW.embedding IS NOT NULL THEN
                        NEW.embedding = l2_normalize(NEW.embedding);
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """))

            # Then drop the trigger if it exists
            await session.execute(text("""
                DROP TRIGGER IF EXISTS normalize_embedding ON messages;
            """))

            # Finally create the trigger
            await session.execute(text("""
                CREATE TRIGGER normalize_embedding
                    BEFORE INSERT OR UPDATE ON messages
                    FOR EACH ROW
                    EXECUTE FUNCTION normalize_vector();
            """))

            await session.commit()
            click.echo("Migration completed successfully")

    try:
        asyncio.run(run())
    except Exception as e:
        click.echo(f"Migration failed: {str(e)}", err=True)
        raise

@db.command()
def verify_schema():
    """Verify database schema"""
    async def run():
        async with get_session() as session:
            # Check column information
            result = await session.execute(text("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'messages'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()

            click.echo("\nCurrent schema for messages table:")
            for col in columns:
                click.echo(f"{col[0]}: {col[1]}" +
                          (f" (max length: {col[2]})" if col[2] else ""))

    asyncio.run(run())

@db.command()
def fix_dimensions():
    """Fix vector dimensions and triggers in database"""
    async def run():
        from humanizer.config import get_settings
        settings = get_settings()

        async with get_session() as session:
            try:
                # Drop trigger first
                await session.execute(text(
                    "DROP TRIGGER IF EXISTS normalize_embedding ON messages;"
                ))
                await session.commit()

                # Drop function
                await session.execute(text(
                    "DROP FUNCTION IF EXISTS normalize_vector();"
                ))
                await session.commit()

                # Drop embedding column
                await session.execute(text(
                    "ALTER TABLE messages DROP COLUMN IF EXISTS embedding;"
                ))
                await session.commit()

                # Add embedding column with correct dimensions
                await session.execute(text(
                    f"ALTER TABLE messages ADD COLUMN embedding vector({settings.embedding_dimensions});"
                ))
                await session.commit()

                # Ensure model column exists
                await session.execute(text(
                    "ALTER TABLE messages ADD COLUMN IF NOT EXISTS embedding_model VARCHAR;"
                ))
                await session.commit()

                # Create normalization function
                await session.execute(text("""
                    CREATE OR REPLACE FUNCTION normalize_vector()
                    RETURNS trigger AS $$
                    BEGIN
                        IF NEW.embedding IS NOT NULL THEN
                            NEW.embedding = l2_normalize(NEW.embedding);
                        END IF;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """))
                await session.commit()

                # Create trigger
                await session.execute(text("""
                    CREATE TRIGGER normalize_embedding
                        BEFORE INSERT OR UPDATE ON messages
                        FOR EACH ROW
                        EXECUTE FUNCTION normalize_vector();
                """))
                await session.commit()

                click.echo(f"Vector column updated to {settings.embedding_dimensions} dimensions with normalization")

            except Exception as e:
                click.echo(f"Error during operation: {str(e)}")
                await session.rollback()
                raise

    try:
        asyncio.run(run())
    except Exception as e:
        click.echo(f"Error updating schema: {str(e)}", err=True)
        raise

@db.command()
def verify_setup():
    """Verify database setup"""
    async def run():
        async with get_session() as session:
            # Check column existence
            result = await session.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'messages'
                AND column_name IN ('embedding', 'embedding_model');
            """))
            columns = result.fetchall()

            click.echo("\nColumns:")
            for col in columns:
                click.echo(f"✓ {col[0]}: {col[1]}")

            # Check trigger
            result = await session.execute(text("""
                SELECT trigger_name
                FROM information_schema.triggers
                WHERE event_object_table = 'messages';
            """))
            triggers = result.fetchall()

            click.echo("\nTriggers:")
            for trigger in triggers:
                click.echo(f"✓ {trigger[0]}")

    asyncio.run(run())
