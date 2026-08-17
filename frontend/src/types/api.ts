export type RetrievalMode = "semantic" | "bm25" | "hybrid" | "hybrid_rerank";
export type Confidence = "High" | "Medium" | "Low" | "Insufficient Evidence";
export type GoldenCategory = "direct" | "multi_chunk" | "ambiguous" | "out_of_scope";

export interface ChunkMetadata {
  document_name: string;
  page_number: number;
  section_title: string;
  chunk_id: string;
  source_url: string;
  doc_key: string;
  section_path: string[];
  page_end: number | null;
  token_count: number;
  recommendation_ids: string[];
  has_cross_reference: boolean;
  printed_page: number | null;
}

export interface Chunk {
  text: string;
  metadata: ChunkMetadata;
}

export interface ScoredChunk {
  chunk: Chunk;
  score: number;
  source: RetrievalMode;
}

export interface RetrievalResult {
  query: string;
  mode: RetrievalMode;
  k: number;
  results: ScoredChunk[];
}

export interface GateDecision {
  verdict: "ALLOW" | "CAUTION" | "REFUSE";
  reason: string;
  triggered_by: string | null;
}

export interface ThresholdDecision {
  action: "PROCEED" | "DOWNGRADE" | "HALT";
  top_score: number;
  reason: string;
}

export interface QuoteCheck {
  chunk_id: string;
  quote: string;
  verified: boolean;
  match_ratio: number;
}

export interface ClaimSupport {
  claim: string;
  supported: boolean;
}

export interface ClaimAudit {
  quote_checks: QuoteCheck[];
  claims: ClaimSupport[];
  unsupported_rate: number;
}

export interface EvidenceItem {
  quote: string;
  chunk_id: string;
}

export interface GroundedAnswer {
  recommendation: string;
  evidence: EvidenceItem[];
  insufficient_evidence: boolean;
  caveats: string[];
}

export interface Citation {
  document_name: string;
  section_title: string;
  page_number: number;
  chunk_id: string;
}

export interface FinalAnswer {
  recommendation: string;
  evidence: EvidenceItem[];
  citations: Citation[];
  confidence: Confidence;
  disclaimer: string;
}

export interface AnswerTrace {
  query: string;
  gate: GateDecision;
  retrieval: RetrievalResult | null;
  threshold: ThresholdDecision | null;
  raw_answer: GroundedAnswer | null;
  audit: ClaimAudit | null;
  final: FinalAnswer;
  timings_ms: Record<string, number>;
}

export interface IngestResult {
  doc_key: string;
  chunk_count: number;
  indexed_vector_count: number;
  pages_path: string;
  chunks_path: string;
}

export interface IngestResponse {
  results: IngestResult[];
}

export interface RetrievalMatrixRow {
  mode: RetrievalMode;
  k: number;
  precision_at_k: number;
  recall_at_k: number;
  mrr: number;
  n_questions_scored: number;
}

export interface ScoreDistribution {
  answerable_top_scores: number[];
  out_of_scope_top_scores: number[];
  insufficient_top_scores: number[];
}

export interface RetrievalEvalReport {
  report_path: string;
  timestamp: string;
  golden_set_size: number;
  matrix: RetrievalMatrixRow[];
  score_distributions: Record<RetrievalMode, ScoreDistribution>;
}

export interface EvalFailure {
  qid: string;
  question: string;
  category: string;
  expected_behavior: string;
  actual_gate_verdict: string | null;
  actual_confidence: string | null;
  relevant_chunk_ids: string[];
  retrieved_chunk_ids: string[];
  error?: string;
}

export interface E2EEvalReport {
  report_path: string;
  timestamp: string;
  golden_set_size: number;
  mode: RetrievalMode;
  k: number;
  precision_at_k: number;
  recall_at_k: number;
  mrr: number;
  n_questions_scored: number;
  citation_accuracy: number;
  unsupported_claim_rate: number;
  refusal_correctness: number;
  category_breakdown: Record<GoldenCategory, { count: number; correct: number }>;
  failures: EvalFailure[];
}
