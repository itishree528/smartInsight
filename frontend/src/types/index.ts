export interface Document {
  id: string;
  filename: string;
  file_size: number;
  total_pages: number;
  chunk_count: number;
  created_at: string;
}

export interface Citation {
  document_id: string;
  document_name: string;
  chunk_index: number;
  page_number: number;
  text_content: string;
  similarity_score: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  ttft_ms?: number;
  total_time_ms?: number;
  cache_hit?: boolean;
  timestamp: number;
  isStreaming?: boolean;
}

export interface AnalyticsStats {
  total_documents: number;
  total_chunks: number;
  total_queries: number;
  cache_hits: number;
  cache_misses: number;
  cache_hit_rate: number;
  api_overhead_saved_pct: number;
  average_ttft_ms: number;
  vector_dimension: number;
}

export type UploadStep =
  | "idle"
  | "uploading"
  | "parsing"
  | "chunking"
  | "indexing"
  | "completed"
  | "error";
