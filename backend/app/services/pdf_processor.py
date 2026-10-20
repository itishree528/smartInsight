import io
import re
from typing import List, Dict, Any
from pypdf import PdfReader


class PDFProcessor:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text_by_pages(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """Extracts text page by page from raw PDF bytes."""
        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)
        pages_data = []

        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            # Clean excessive whitespace while preserving paragraphs
            cleaned_text = re.sub(r"\s+", " ", text).strip()
            if cleaned_text:
                pages_data.append({
                    "page_number": idx + 1,
                    "text": cleaned_text,
                })

        return pages_data

    def chunk_text(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Splits extracted page text into overlapping semantic chunks with
        preserved page metadata.
        """
        chunks: List[Dict[str, Any]] = []
        chunk_idx = 0

        for page in pages_data:
            page_text = page["text"]
            page_num = page["page_number"]

            start = 0
            text_length = len(page_text)

            while start < text_length:
                end = start + self.chunk_size
                chunk_str = page_text[start:end]

                # If we're not at the end of the text, try to break cleanly at sentence or word boundary
                if end < text_length:
                    last_period = chunk_str.rfind(". ")
                    last_space = chunk_str.rfind(" ")
                    if last_period > self.chunk_size * 0.6:
                        chunk_str = chunk_str[: last_period + 1]
                        end = start + last_period + 1
                    elif last_space > self.chunk_size * 0.6:
                        chunk_str = chunk_str[:last_space]
                        end = start + last_space

                chunk_str = chunk_str.strip()
                if len(chunk_str) > 30:  # Skip trivial chunks
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "page_number": page_num,
                        "text_content": chunk_str,
                        "token_count": len(chunk_str.split()),
                    })
                    chunk_idx += 1

                # Advance with overlap
                start = end - self.chunk_overlap
                if start >= text_length or end >= text_length:
                    break

        return chunks


pdf_processor = PDFProcessor()
