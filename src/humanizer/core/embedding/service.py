# src/humanizer/core/embedding/service.py
from typing import List
import httpx
from humanizer.config import get_settings
from humanizer.utils.logging import get_logger

logger = get_logger(__name__)

class EmbeddingService:
    def __init__(self):
        self.settings = get_settings()
        self.embedding_model = self.settings.embedding_model
        self.embedding_dimensions = self.settings.embedding_dimensions
        logger.info(f"Initializing EmbeddingService with model={self.embedding_model}, dims={self.embedding_dimensions}")

    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding vector for text using Ollama."""
        try:
            # Add task prefix for proper instruction
            prefixed_text = f"search_document: {text}"

            logger.debug(f"Creating embedding for text length {len(prefixed_text)}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.settings.ollama_base_url}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": prefixed_text,
                        "options": {
                            "num_ctx": 8192  # Support longer context
                        }
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                if 'error' in data:
                    raise ValueError(f"Ollama API error: {data['error']}")

                embedding = data.get("embedding", [])
                if not embedding:
                    logger.error(f"No embedding in response. Full response: {data}")
                    raise ValueError("No embedding returned from API")

                # Handle Matryoshka dimensionality
                if len(embedding) > self.embedding_dimensions:
                    embedding = embedding[:self.embedding_dimensions]
                elif len(embedding) < self.embedding_dimensions:
                    logger.error(f"Model returned {len(embedding)} dimensions, expected {self.embedding_dimensions}")
                    raise ValueError("Insufficient dimensions from model")

                return embedding

        except httpx.HTTPError as e:
            logger.error(f"HTTP error while calling Ollama API: {str(e)}")
            raise ValueError(f"HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create embedding: {str(e)}")
            raise

    async def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            if not text.strip():  # Skip empty texts
                logger.warning("Skipping empty text")
                continue
            embedding = await self.create_embedding(text)
            embeddings.append(embedding)
        return embeddings
