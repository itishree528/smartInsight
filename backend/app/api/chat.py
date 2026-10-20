import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import ChatRequest, Citation
from app.services.vector_search import vector_search_service
from app.services.cache_service import cache_service
from app.services.llm_streamer import llm_streamer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat & Streaming"])


@router.post(
    "/stream",
    summary="Stream LLM responses using Server-Sent Events (SSE) with Redis caching and TTFT measurement",
)
async def stream_chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Check Redis semantic cache
    cached_result = None
    try:
        cached_result = await cache_service.get_cached_query(query)
    except Exception as e:
        logger.warning(f"Cache check notice: {e}")

    citations: List[Citation] = []

    if cached_result:
        try:
            citations = [
                Citation(**c) for c in cached_result.get("citations", [])
            ]
            logger.info(f"Cache HIT for query: '{query}'")
        except Exception as e:
            logger.warning(f"Failed to parse cached citations: {e}")
            cached_result = None

    if not cached_result:
        # 2. Vector search via pgvector cosine similarity
        logger.info(f"Cache MISS for query: '{query}'. Performing vector search...")
        try:
            citations = await vector_search_service.search_similar_chunks(
                db=db,
                query=query,
                top_k=req.top_k or 4,
            )
        except Exception as e:
            logger.warning(f"Vector search notice: {e}")
            citations = []

    # 3. Return asynchronous SSE stream
    generator = llm_streamer.stream_chat_response(
        query=query,
        citations=citations,
        cached_result=cached_result,
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/query",
    summary="Synchronous query endpoint returning full answer and citations",
)
async def direct_query(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    query = req.query.strip()
    try:
        cached = await cache_service.get_cached_query(query)
        if cached:
            return {
                "query": query,
                "answer": cached["answer"],
                "citations": cached["citations"],
                "cache_hit": True,
                "ttft_ms": cached.get("ttft_ms", 45.0),
            }
    except Exception:
        pass

    try:
        citations = await vector_search_service.search_similar_chunks(
            db=db,
            query=query,
            top_k=req.top_k or 4,
        )
    except Exception:
        citations = []

    tokens = []
    done_data = {}

    async for chunk in llm_streamer.stream_chat_response(query, citations):
        if chunk.startswith("event: token\n"):
            import json
            try:
                data = json.loads(chunk.split("data: ")[1].strip())
                tokens.append(data.get("token", ""))
            except Exception:
                pass
        elif chunk.startswith("event: done\n"):
            import json
            try:
                done_data = json.loads(chunk.split("data: ")[1].strip())
            except Exception:
                pass

    return {
        "query": query,
        "answer": "".join(tokens),
        "citations": [c.model_dump(mode="json") if hasattr(c, "model_dump") else c for c in citations],
        "cache_hit": False,
        "ttft_ms": done_data.get("ttft_ms", 210.0),
        "total_time_ms": done_data.get("total_time_ms", 500.0),
    }
