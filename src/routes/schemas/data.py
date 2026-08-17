from typing import Optional

from pydantic import BaseModel


class IngestRequest(BaseModel):
    doc_keys: Optional[list[str]] = None
    target_tokens: Optional[int] = None
    hard_max_tokens: Optional[int] = None
    min_tokens: Optional[int] = None
    overlap_tokens: Optional[int] = None


class IngestResult(BaseModel):
    doc_key: str
    chunk_count: int
    indexed_vector_count: int
    pages_path: str
    chunks_path: str


class IngestResponse(BaseModel):
    results: list[IngestResult]
