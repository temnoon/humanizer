# src/humanizer/core/search/vector.py
from typing import List, Dict, Optional
from sqlalchemy import select, func, and_
from humanizer.db.models import Message, Content
from humanizer.db.session import get_session
from humanizer.core.embedding.service import EmbeddingService

class VectorSearch:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    async def search(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        role: Optional[str] = None
    ) -> List[Dict]:
        """Search messages using vector similarity"""
        query_embedding = await self.embedding_service.create_embedding(query)

        async with get_session() as session:
            stmt = select(
                Message,
                Message.embedding.cosine_distance(query_embedding).label('distance')
            ).where(
                and_(
                    Message.embedding.is_not(None),
                    Message.content.notlike('%{"query"%'),  # Filter out JSON-formatted messages
                    Message.content != '',
                    Message.content.is_not(None)
                )
            )

            if role:
                stmt = stmt.where(Message.role == role)

            stmt = stmt.where(
                Message.embedding.cosine_distance(query_embedding) <= (1 - min_similarity)
            )

            stmt = stmt.order_by('distance').limit(limit)

            results = await session.execute(stmt)
            messages = results.all()

            return [
                {
                    "id": msg.Message.id,
                    "content": msg.Message.content,
                    "role": msg.Message.role,
                    "conversation_id": msg.Message.conversation_id,
                    "similarity": 1 - msg.distance
                }
                for msg in messages
            ]

    async def find_similar_conversations(
        self,
        conversation_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """Find conversations similar to the given one"""
        async with get_session() as session:
            # First get the target conversation's messages
            target_msgs = await session.execute(
                select(Message.embedding)
                .where(Message.conversation_id == conversation_id)
                .where(Message.embedding.is_not(None))
            )

            # Calculate average embedding manually
            embeddings = [msg[0] for msg in target_msgs.fetchall()]
            if not embeddings:
                return []

            avg_embedding = [sum(x)/len(embeddings) for x in zip(*embeddings)]

            # Find similar conversations
            stmt = (
                select(
                    Content,
                    func.avg(Message.embedding.cosine_distance(avg_embedding)).label('avg_distance')
                )
                .join(Message, Content.id == Message.conversation_id)
                .where(Content.id != conversation_id)
                .where(Message.embedding.is_not(None))
                .group_by(Content.id)
                .order_by('avg_distance')
                .limit(limit)
            )

            results = await session.execute(stmt)
            conversations = results.all()

            return [
                {
                    "id": conv.Content.id,
                    "title": conv.Content.title,
                    "similarity": 1 - conv.avg_distance
                }
                for conv in conversations
            ]
