from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    document_name: str
    page_number: int
    section_title: str
    chunk_id: str
    source_url: str

    doc_key: str
    section_path: list[str] = Field(default_factory=list)
    page_end: Optional[int] = None
    token_count: int
    recommendation_ids: list[str] = Field(default_factory=list)
    has_cross_reference: bool = False
    printed_page: Optional[int] = None


class Chunk(BaseModel):
    text: str
    metadata: ChunkMetadata


class CleanedPage(BaseModel):
    doc_key: str
    page_number: int
    printed_page: Optional[int] = None
    text: str
    section_title: str
    section_path: list[str] = Field(default_factory=list)
    recommendation_ids: list[str] = Field(default_factory=list)


RetrievalMode = Literal["semantic", "bm25", "hybrid", "hybrid_rerank"]


class ScoredChunk(BaseModel):
    chunk: Chunk
    score: float
    source: RetrievalMode


class RetrievalResult(BaseModel):
    query: str
    mode: RetrievalMode
    k: int
    results: list[ScoredChunk] = Field(default_factory=list)


class GateDecision(BaseModel):
    verdict: Literal["ALLOW", "CAUTION", "REFUSE"]
    reason: str
    triggered_by: Optional[str] = None


class ThresholdDecision(BaseModel):
    action: Literal["PROCEED", "DOWNGRADE", "HALT"]
    top_score: float
    reason: str


class QuoteCheck(BaseModel):
    chunk_id: str
    quote: str
    verified: bool
    match_ratio: float


class ClaimSupport(BaseModel):
    claim: str
    supported: bool


class ClaimAudit(BaseModel):
    quote_checks: list[QuoteCheck] = Field(default_factory=list)
    claims: list[ClaimSupport] = Field(default_factory=list)
    unsupported_rate: float


class EvidenceItem(BaseModel):
    quote: str
    chunk_id: str


class GroundedAnswer(BaseModel):
    recommendation: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    insufficient_evidence: bool
    caveats: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    document_name: str
    section_title: str
    page_number: int
    chunk_id: str


Confidence = Literal["High", "Medium", "Low", "Insufficient Evidence"]


class FinalAnswer(BaseModel):
    recommendation: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence: Confidence
    disclaimer: str


class AnswerTrace(BaseModel):
    query: str
    gate: GateDecision
    retrieval: Optional[RetrievalResult] = None
    threshold: Optional[ThresholdDecision] = None
    raw_answer: Optional[GroundedAnswer] = None
    audit: Optional[ClaimAudit] = None
    final: FinalAnswer
    timings_ms: dict[str, float] = Field(default_factory=dict)


class GoldenAnchor(BaseModel):
    chunk_id: str
    anchor_text: str


class GoldenQuestion(BaseModel):
    qid: str
    question: str
    category: Literal["direct", "multi_chunk", "ambiguous", "out_of_scope"]
    relevant_chunk_ids: list[str] = Field(default_factory=list)
    anchors: list[GoldenAnchor] = Field(default_factory=list)
    expected_behavior: Literal["answer", "refuse", "insufficient"]
    notes: str = ""
