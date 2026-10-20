import hashlib
import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.models.schemas import (
    DocumentRead,
    DocumentChunkRead,
    DocumentUploadResponse,
)
from app.services.pdf_processor import pdf_processor
from app.services.embedding_service import embedding_service
from app.services.cache_service import cache_service
from app.services import local_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF, chunk text, compute dense embeddings, and store in pgvector",
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported.",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    content_hash = hashlib.sha256(content).hexdigest()

    # 1. Extract text page-by-page using pypdf
    try:
        pages_data = pdf_processor.extract_text_by_pages(content)
        if not pages_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No readable text could be extracted from this PDF.",
            )
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse PDF: {str(e)}",
        )

    # 2. Chunk text with semantic overlap
    chunks_meta = pdf_processor.chunk_text(pages_data)
    if not chunks_meta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document contained insufficient text for chunking.",
        )

    # 3. Compute dense vector embeddings (1536-dim)
    await cache_service.clear_cache()
    local_store.clear_query_cache()
    texts_to_embed = [c["text_content"] for c in chunks_meta]
    embeddings = await embedding_service.get_embeddings(texts_to_embed)

    # 4. Save to persistent SQLite storage (Guarantees persistence across reloads & browser refreshes!)
    saved_doc = local_store.save_document(
        filename=file.filename,
        file_size=len(content),
        total_pages=len(pages_data),
        chunks_meta=chunks_meta,
        embeddings=embeddings,
        content_hash=content_hash,
    )

    # 5. Also try storing in PostgreSQL with pgvector if connected
    try:
        doc = Document(
            filename=file.filename,
            file_size=len(content),
            total_pages=len(pages_data),
            chunk_count=len(chunks_meta),
            content_hash=content_hash,
        )
        db.add(doc)
        await db.flush()

        db_chunks = []
        for meta, emb in zip(chunks_meta, embeddings):
            chunk_obj = DocumentChunk(
                document_id=doc.id,
                chunk_index=meta["chunk_index"],
                page_number=meta["page_number"],
                text_content=meta["text_content"],
                token_count=meta["token_count"],
                embedding=emb,
            )
            db_chunks.append(chunk_obj)

        db.add_all(db_chunks)
        await db.commit()
    except Exception as db_err:
        logger.warning(
            f"Notice: PostgreSQL write bypassed ({db_err}). Document safely saved to persistent local store."
        )

    doc_read = DocumentRead(
        id=UUID(saved_doc["id"]),
        filename=saved_doc["filename"],
        file_size=saved_doc["file_size"],
        total_pages=saved_doc["total_pages"],
        chunk_count=saved_doc["chunk_count"],
        created_at=saved_doc["created_at"],
    )

    return DocumentUploadResponse(
        document=doc_read,
        chunks_created=len(chunks_meta),
        message=f"Successfully extracted {len(pages_data)} pages, generated {len(chunks_meta)} chunks, and saved vectors.",
    )


@router.get(
    "",
    response_model=List[DocumentRead],
    summary="List all indexed documents",
)
async def list_documents(db: AsyncSession = Depends(get_db)):
    # 1. Try PostgreSQL
    try:
        result = await db.execute(select(Document).order_by(Document.created_at.desc()))
        docs = result.scalars().all()
        if docs:
            return [DocumentRead.model_validate(d) for d in docs]
    except Exception:
        pass

    # 2. Return from persistent SQLite disk storage (Never disappears on refresh!)
    local_docs = local_store.get_all_documents()
    return [
        DocumentRead(
            id=UUID(d["id"]),
            filename=d["filename"],
            file_size=d["file_size"],
            total_pages=d["total_pages"],
            chunk_count=d["chunk_count"],
            created_at=d["created_at"],
        )
        for d in local_docs
    ]


@router.get(
    "/{document_id}/chunks",
    response_model=List[DocumentChunkRead],
    summary="Inspect chunks for a specific document",
)
async def get_document_chunks(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        chunks = result.scalars().all()
        if chunks:
            return [DocumentChunkRead.model_validate(c) for c in chunks]
    except Exception:
        pass

    # Fallback to local store
    local_chunks = local_store.get_document_chunks_by_id(str(document_id))
    if not local_chunks:
        raise HTTPException(status_code=404, detail="Document chunks not found.")

    return [
        DocumentChunkRead(
            id=UUID(c["id"]),
            chunk_index=c["chunk_index"],
            page_number=c["page_number"],
            text_content=c["text_content"],
            token_count=c["token_count"],
        )
        for c in local_chunks
    ]


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its vector embeddings",
)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        await db.execute(delete(Document).where(Document.id == document_id))
        await db.commit()
    except Exception:
        pass

    local_store.delete_document_by_id(str(document_id))
    return None
