from typing import Optional

from pydantic import BaseModel

from src.core.schemas import RetrievalMode


class SearchRequest(BaseModel):
    query: str
    mode: RetrievalMode = "hybrid_rerank"
    k: Optional[int] = None


class AnswerRequest(BaseModel):
    query: str
    mode: RetrievalMode = "hybrid_rerank"
    k: Optional[int] = None
