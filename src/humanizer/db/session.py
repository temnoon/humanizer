# src/humanizer/db/session.py
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from humanizer.utils.logging import get_logger
from humanizer.config import get_settings # This line changed
from humanizer.config.database import DatabaseRole


logger = get_logger(__name__)

async def init_db(force: bool = False) -> None:
    """Initialize database schema"""
    from humanizer.db.models.base import Base
    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    async with engine.begin() as conn:
        if force:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")

@asynccontextmanager
async def get_session(role: DatabaseRole = DatabaseRole.APP) -> AsyncGenerator[AsyncSession, None]: # This line changed
    """Get database session with appropriate role"""
    settings = get_settings() # This line changed

    engine = create_async_engine(
        settings.database_url, # This line changed
        poolclass=NullPool,
        echo=False,
    )
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

__all__ = ['init_db', 'get_session']
