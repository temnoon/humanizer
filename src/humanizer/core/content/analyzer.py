# src/humanizer/core/content/analyzer.py
from typing import List, Tuple
import math
from uuid import UUID
from sqlalchemy import select
from humanizer.db.session import get_session
from humanizer.db.models import Message
from humanizer.core.embedding.service import EmbeddingService

class ConversationAnalyzer:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    async def get_conversation_embedding(
        self,
        conversation_id: UUID,
        weighting: str = "average"
    ) -> List[float]:
        """
        Compute a single vector representing the entire conversation.

        Parameters:
            conversation_id: UUID of the conversation
            weighting: "average" or another scheme you might implement like TF-IDF

        Returns:
            A single embedding vector as a list of floats representing the conversation.
        """
        async with get_session() as session:
            # Fetch embeddings of all messages in the conversation
            result = await session.execute(
                select(Message.embedding, Message.content)
                .where(Message.conversation_id == conversation_id)
                .where(Message.embedding.isnot(None))
            )
            rows = result.all()

        if not rows:
            # If no embeddings found, return a zero vector or raise an exception
            return [0.0] * self.embedding_service.embedding_dimensions

        embeddings = [r[0] for r in rows]
        contents = [r[1] for r in rows]

        # Simple averaging
        # embeddings is a list of lists: [[float], [float], ...]
        # We assume all are normalized embeddings (or at least same dimension)
        dim = len(embeddings[0])
        sum_vec = [0.0] * dim
        count = len(embeddings)

        # Basic averaging approach
        for emb in embeddings:
            for i, val in enumerate(emb):
                sum_vec[i] += val

        # Divide by count to get the average
        avg_vec = [v / count for v in sum_vec]

        # If embeddings are normalized vectors, consider re-normalizing the final average
        # to maintain a consistent scale:
        norm = math.sqrt(sum(x * x for x in avg_vec))
        if norm > 0:
            avg_vec = [x / norm for x in avg_vec]

        return avg_vec

    async def find_most_characteristic_message(
            self,
            conversation_id: UUID
        ) -> Tuple[str, float]:
            """
            Find the most characteristic message of a conversation by:
            1. Getting the conversation-level embedding.
            2. Finding the message whose embedding is most similar to the conversation vector.

            Returns:
                A tuple (message_content, similarity_score) for the most characteristic message.
            """
            conversation_embedding = await self.get_conversation_embedding(conversation_id)

            async with get_session() as session:
                # Retrieve messages and embeddings for this conversation
                result = await session.execute(
                    select(Message.content, Message.embedding)
                    .where(Message.conversation_id == conversation_id)
                    .where(Message.embedding.isnot(None))
                    .where(Message.content.isnot(None))
                )
                messages = result.all()

            if not messages:
                raise ValueError("No embeddings found for this conversation.")

            # Compute cosine similarity
            # cosine similarity = 1 - cosine_distance
            # But we can compute directly: sim(u,v) = (u·v)/(||u||*||v||)
            # Since we normalized average, and assuming messages are also normalized (due to triggers),
            # similarity = dot product if both are normalized.

            best_msg: str = messages[0][0]  # Initialize with first message content
            best_sim: float = -1.0

            for (content, emb) in messages:
                # Dot product for similarity (assuming normalized)
                sim = sum(a * b for a, b in zip(conversation_embedding, emb))
                if sim > best_sim:
                    best_sim = sim
                    best_msg = content

            return best_msg, best_sim
