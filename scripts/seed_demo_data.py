"""
SmartInsight Seed Script
Populates the database with initial demo document chunks and seeds the Redis cache
so you can immediately test pgvector cosine search and citation cards.
"""

import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import AsyncSessionLocal, init_db
from app.models.document import Document, DocumentChunk
from app.services.embedding_service import embedding_service
from app.services.cache_service import cache_service
from sqlalchemy import select


DEMO_CHUNKS = [
    {
        "page_number": 1,
        "text": (
            "SmartInsight implements a high-throughput RAG retrieval architecture utilizing PostgreSQL with the "
            "pgvector extension. Uploaded documents are parsed into overlapping chunks of 600 characters with 120 character "
            "overlaps to preserve contextual boundaries. Dense vector embeddings with 1536 dimensions are generated and indexed "
            "using an HNSW (Hierarchical Navigable Small World) index with vector_cosine_ops."
        ),
    },
    {
        "page_number": 1,
        "text": (
            "Cosine similarity search is computed using the <=> cosine distance operator in pgvector. Distance values "
            "range from 0 (identical) to 2 (opposing), where similarity score is calculated as 1 - distance. Top-K nearest "
            "neighbors are returned in under 15ms even over collections exceeding 100,000 vectors."
        ),
    },
    {
        "page_number": 2,
        "text": (
            "To achieve ultra-low latency, FastAPI endpoints utilize asynchronous streaming generators coupled with "
            "Server-Sent Events (SSE). This reduces Time-to-First-Token (TTFT) to less than 350ms, delivering instantaneous "
            "feedback to the Next.js client before the entire language model generation is completed."
        ),
    },
    {
        "page_number": 3,
        "text": (
            "The multi-tier caching system features an asynchronous Redis layer that intercepts repeated semantic queries. "
            "In production benchmarks, this caching architecture achieved a 68% cache hit rate, directly cutting external "
            "LLM API overhead and inference cost by 40% while returning cached answers in under 50ms."
        ),
    },
]


async def seed():
    print("Connecting and initializing database...")
    await init_db()
    await cache_service.connect()

    async with AsyncSessionLocal() as session:
        # Check if demo doc exists
        result = await session.execute(
            select(Document).where(Document.filename == "smartinsight_architecture_whitepaper.pdf")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("Demo document already exists. Skipping document seed.")
        else:
            print("Creating demo document: smartinsight_architecture_whitepaper.pdf...")
            doc = Document(
                filename="smartinsight_architecture_whitepaper.pdf",
                file_size=1048576,
                total_pages=3,
                chunk_count=len(DEMO_CHUNKS),
                content_hash="seed_demo_hash_987654321",
            )
            session.add(doc)
            await session.flush()

            texts = [c["text"] for c in DEMO_CHUNKS]
            print(f"Generating 1536-dim embeddings for {len(texts)} chunks...")
            embeddings = await embedding_service.get_embeddings(texts)

            chunks = []
            for idx, (data, emb) in enumerate(zip(DEMO_CHUNKS, embeddings)):
                chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    page_number=data["page_number"],
                    text_content=data["text"],
                    token_count=len(data["text"].split()),
                    embedding=emb,
                )
                chunks.append(chunk)

            session.add_all(chunks)
            await session.commit()
            print("Document and vector chunks indexed successfully in pgvector!")

    # Pre-populate sample cached query
    print("Seeding Redis cache for benchmark demonstration...")
    sample_query = "What is the cache hit rate and TTFT latency?"
    sample_answer = (
        "According to the whitepaper, SmartInsight achieves a **68% cache hit rate** via its Redis caching layer, "
        "which reduces external API overhead by **40%**. Furthermore, asynchronous FastAPI streaming with Server-Sent Events "
        "reduces Time-to-First-Token (TTFT) to **<350ms**."
    )
    sample_citations = [
        {
            "document_id": "00000000-0000-0000-0000-000000000001",
            "document_name": "smartinsight_architecture_whitepaper.pdf",
            "chunk_index": 3,
            "page_number": 3,
            "text_content": DEMO_CHUNKS[3]["text"],
            "similarity_score": 0.942,
        }
    ]
    await cache_service.set_cached_query(
        query=sample_query,
        answer=sample_answer,
        citations=sample_citations,
        ttft_ms=45.0,
    )
    print("Seed complete! You can now start the application.")
    await cache_service.close()


if __name__ == "__main__":
    asyncio.run(seed())
