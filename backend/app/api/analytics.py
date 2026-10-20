from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.models.schemas import AnalyticsStats
from app.services.cache_service import cache_service
from app.services import local_store
from app.config import settings

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/stats",
    response_model=AnalyticsStats,
    summary="Get real-time cache hit rate, TTFT metrics, and document stats",
)
async def get_analytics_stats(db: AsyncSession = Depends(get_db)):
    total_docs = 0
    total_chunks = 0

    try:
        doc_count_res = await db.execute(select(func.count(Document.id)))
        total_docs = doc_count_res.scalar_one() or 0

        chunk_count_res = await db.execute(select(func.count(DocumentChunk.id)))
        total_chunks = chunk_count_res.scalar_one() or 0
    except Exception:
        pass

    if total_docs == 0:
        local_docs = local_store.get_all_documents()
        total_docs = len(local_docs)
        total_chunks = sum(d["chunk_count"] for d in local_docs)

    stats = await cache_service.get_stats()

    return AnalyticsStats(
        total_documents=total_docs,
        total_chunks=total_chunks,
        total_queries=stats["total_queries"],
        cache_hits=stats["cache_hits"],
        cache_misses=stats["cache_misses"],
        cache_hit_rate=stats["cache_hit_rate"],
        api_overhead_saved_pct=stats["api_overhead_saved_pct"],
        average_ttft_ms=stats["average_ttft_ms"],
        vector_dimension=settings.EMBEDDING_DIMENSION,
    )
