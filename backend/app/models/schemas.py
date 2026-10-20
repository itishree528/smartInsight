from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field


class DocumentChunkRead(BaseModel):
    id: UUID
    chunk_index: int
    page_number: int
    text_content: str
    token_count: int

    class Config:
        from_attributes = True


class DocumentRead(BaseModel):
    id: UUID
    filename: str
    file_size: int
    total_pages: int
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    document: DocumentRead
    chunks_created: int
    message: str


class Citation(BaseModel):
    document_id: Union[UUID, str]
    document_name: str
    chunk_index: int
    page_number: int
    text_content: str
    similarity_score: float = Field(
        ...,
        description="Cosine similarity percentage (0.0 to 1.0)",
    )


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1500)
    top_k: Optional[int] = Field(default=4, ge=1, le=10)
    stream: bool = True


class AnalyticsStats(BaseModel):
    total_documents: int
    total_chunks: int
    total_queries: int
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float = Field(
        description="Cache hit percentage e.g. 68.0",
    )
    api_overhead_saved_pct: float = Field(
        description="External API overhead saved percentage e.g. 40.0",
    )
    average_ttft_ms: float = Field(
        description="Average Time to First Token in ms (e.g. 210ms < 350ms)",
    )
    vector_dimension: int
