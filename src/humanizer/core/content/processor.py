# src/humanizer/core/content/processor.py
from typing import AsyncIterator, List, Sequence
from sqlalchemy import select, func, and_, true
from sqlalchemy.ext.asyncio import AsyncSession
from humanizer.db.models import Message
from humanizer.db.session import get_session
from humanizer.core.embedding.service import EmbeddingService
from humanizer.utils.logging import get_logger

logger = get_logger(__name__)

class ContentProcessor:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    async def count_pending_embeddings(self, force: bool = False) -> int:
        """Count messages that need embedding updates"""
        async with get_session() as session:
            query = select(func.count()).select_from(Message)
            if not force:
                query = query.where(Message.embedding.is_(None))
            return await session.scalar(query) or 0

    async def get_embedding_stats(self) -> dict:
        """Get embedding statistics"""
        async with get_session() as session:
            total = await session.scalar(
                select(func.count()).select_from(Message)
            ) or 0

            embedded = await session.scalar(
                select(func.count())
                .select_from(Message)
                .where(Message.embedding.isnot(None))
            ) or 0

            return {
                'total': total,
                'embedded': embedded,
                'pending': total - embedded
            }

    async def update_embeddings(
        self,
        batch_size: int = 50,
        force: bool = False
    ) -> AsyncIterator[int]:
        """Update embeddings for messages that don't have them"""
        async with get_session() as session:
            while True:
                # Get batch of messages without embeddings and with non-empty content
                query = select(Message).where(
                    and_(
                        Message.embedding.is_(None) if not force else true(),
                        Message.content.isnot(None),
                        Message.content != ''
                    )
                ).limit(batch_size)

                result = await session.execute(query)
                messages = result.scalars().all()

                if not messages:
                    break

                # Process each message individually for better error handling
                processed = 0
                for msg in messages:
                    try:
                        if not str(msg.content) or not str(msg.content).strip():
                            logger.debug(f"Skipping empty message {msg.id}")
                            continue

                        embedding = await self.embedding_service.create_embedding(str(msg.content))
                        msg.embedding = embedding
                        msg.embedding_model = self.embedding_service.embedding_model
                        processed += 1

                    except Exception as e:
                        logger.error(f"Error processing message {msg.id}: {str(e)}")
                        continue

                if processed > 0:
                    try:
                        await session.commit()
                        yield processed
                    except Exception as e:
                        logger.error(f"Error committing batch: {str(e)}")
                        await session.rollback()
                else:
                    yield 0
