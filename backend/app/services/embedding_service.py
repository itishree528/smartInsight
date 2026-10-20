import logging
import hashlib
import numpy as np
from typing import List
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.dimension = settings.EMBEDDING_DIMENSION
        self.client = None
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
            try:
                self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("Initialized OpenAI Async Client for Embeddings.")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    def _generate_deterministic_vector(self, text: str) -> List[float]:
        """
        Generates a normalized 1536-dimensional dense embedding vector
        based on token hash projections. Preserves cosine similarity properties
        when running locally without an OpenAI API key.
        """
        # Tokenize and normalize
        tokens = [t.lower() for t in text.split() if len(t) > 2]
        if not tokens:
            tokens = ["empty"]

        vec = np.zeros(self.dimension, dtype=np.float32)

        for token in tokens:
            # Seed from token md5
            token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            rng = np.random.RandomState(token_hash % (2**32))
            # Sample sparse projection
            indices = rng.choice(self.dimension, size=48, replace=False)
            signs = rng.choice([-1.0, 1.0], size=48)
            vec[indices] += signs

        # L2 Normalize vector so cosine distance works properly
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0

        return vec.tolist()

    async def get_embedding(self, text: str) -> List[float]:
        """Compute embedding for a single string."""
        if self.client and not settings.MOCK_LLM_IF_NO_KEY:
            try:
                response = await self.client.embeddings.create(
                    model=settings.EMBEDDING_MODEL,
                    input=text[:8000],
                )
                return response.data[0].embedding
            except Exception as e:
                logger.warning(
                    f"OpenAI embedding call failed ({e}). Falling back to local vector generation."
                )
        return self._generate_deterministic_vector(text)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for a batch of strings."""
        if not texts:
            return []

        if self.client and not settings.MOCK_LLM_IF_NO_KEY:
            try:
                # Truncate each text to safe length
                safe_inputs = [t[:8000] for t in texts]
                response = await self.client.embeddings.create(
                    model=settings.EMBEDDING_MODEL,
                    input=safe_inputs,
                )
                return [d.embedding for d in response.data]
            except Exception as e:
                logger.warning(
                    f"OpenAI batch embedding failed ({e}). Falling back to local vector generation."
                )

        return [self._generate_deterministic_vector(t) for t in texts]


embedding_service = EmbeddingService()
