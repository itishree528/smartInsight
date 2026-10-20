import logging
import re
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentChunk
from app.models.schemas import Citation
from app.services.embedding_service import embedding_service
from app.services import local_store
from app.config import settings

logger = logging.getLogger(__name__)


def compute_keyword_boost(text: str, query: str) -> float:
    """Computes keyword match score (0.0 to 1.0) for hybrid retrieval."""
    q_tokens = set(re.findall(r"\w+", query.lower()))
    stop_words = {
        "what", "is", "the", "how", "much", "have", "has", "a", "an", "in",
        "of", "and", "to", "for", "on", "with", "at", "by", "from", "up",
        "about", "into", "over", "after", "does", "do", "tell", "me"
    }
    keywords = {w for w in q_tokens if len(w) > 1 and w not in stop_words}
    if not keywords:
        return 0.5

    text_lower = text.lower()
    matches = sum(1 for kw in keywords if kw in text_lower)
    return matches / len(keywords)


class VectorSearchService:
    async def search_similar_chunks(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 4,
    ) -> List[Citation]:
        """
        Hybrid retrieval combining dense vector similarity with keyword boosting.
        Searches PostgreSQL with pgvector if online, and falls back to
        the local persistent store.
        """
        # 1. Compute query dense embedding
        query_vector = await embedding_service.get_embedding(query)

        # 2. Try pgvector search via PostgreSQL
        try:
            distance_col = DocumentChunk.embedding.cosine_distance(query_vector).label(
                "distance"
            )

            stmt = (
                select(
                    DocumentChunk,
                    Document.filename,
                    distance_col,
                )
                .join(Document, DocumentChunk.document_id == Document.id)
                .order_by(distance_col)
                .limit(top_k * 3)
            )

            result = await db.execute(stmt)
            rows = result.all()

            if rows:
                scored = []
                for chunk, filename, distance in rows:
                    cos_sim = max(0.0, min(1.0, 1.0 - float(distance)))
                    kw_score = compute_keyword_boost(chunk.text_content, query)
                    hybrid_score = (0.4 * cos_sim) + (0.6 * kw_score)
                    final_score = min(0.98, max(0.20, 0.50 + 0.48 * hybrid_score))

                    scored.append((
                        Citation(
                            document_id=chunk.document_id,
                            document_name=filename,
                            chunk_index=chunk.chunk_index,
                            page_number=chunk.page_number,
                            text_content=chunk.text_content,
                            similarity_score=round(final_score, 4),
                        ),
                        hybrid_score
                    ))

                scored.sort(key=lambda x: x[1], reverse=True)
                return [item[0] for item in scored[:top_k]]
        except Exception as e:
            logger.warning(
                f"PostgreSQL pgvector query notice: {e}. Searching persistent local store."
            )

        # 3. Search persistent local store on disk (Never empty if user uploaded a PDF!)
        local_results = local_store.search_local_chunks(
            query_vector=query_vector,
            query_text=query,
            top_k=top_k,
        )

        citations = []
        for r in local_results:
            citations.append(
                Citation(
                    document_id=r["document_id"],
                    document_name=r["document_name"],
                    chunk_index=r["chunk_index"],
                    page_number=r["page_number"],
                    text_content=r["text_content"],
                    similarity_score=r["similarity_score"],
                )
            )

        return citations


vector_search_service = VectorSearchService()
