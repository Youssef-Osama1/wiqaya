import { http, HttpResponse } from "msw";
import type { AnswerTrace, E2EEvalReport, IngestResponse, RetrievalEvalReport, RetrievalResult } from "@/types/api";

const API_BASE = "http://localhost:8000/api/v1";

export const ALLOW_HIGH_TRACE: AnswerTrace = {
  query: "What is the clinic blood pressure target for people aged 80 and over with hypertension?",
  gate: { verdict: "ALLOW", reason: "In-scope hypertension question.", triggered_by: null },
  retrieval: {
    query: "q",
    mode: "hybrid_rerank",
    k: 5,
    results: [
      {
        chunk: {
          text: "For adults with hypertension aged 80 and over, reduce clinic blood pressure to below 150/90 mmHg.",
          metadata: {
            document_name: "NICE NG136",
            page_number: 16,
            section_title: "Monitoring treatment and blood pressure targets",
            chunk_id: "nice_ng136-p016-beee1ff3",
            source_url: "https://nice.org.uk/ng136",
            doc_key: "nice_ng136",
            section_path: ["Recommendations", "1.4 Treating and monitoring hypertension"],
            page_end: null,
            token_count: 400,
            recommendation_ids: ["1.4.21"],
            has_cross_reference: false,
            printed_page: 16,
          },
        },
        score: 0.938,
        source: "hybrid_rerank",
      },
    ],
  },
  threshold: { action: "PROCEED", top_score: 0.938, reason: "Top retrieval score meets confidence thresholds." },
  raw_answer: {
    recommendation: "For adults with hypertension aged 80 and over, reduce clinic blood pressure to below 150/90 mmHg.",
    evidence: [{ quote: "reduce clinic blood pressure to below 150/90 mmHg", chunk_id: "nice_ng136-p016-beee1ff3" }],
    insufficient_evidence: false,
    caveats: [],
  },
  audit: {
    quote_checks: [{ chunk_id: "nice_ng136-p016-beee1ff3", quote: "reduce clinic blood pressure to below 150/90 mmHg", verified: true, match_ratio: 1.0 }],
    claims: [{ claim: "Target is below 150/90 mmHg for 80+", supported: true }],
    unsupported_rate: 0,
  },
  final: {
    recommendation: "For adults with hypertension aged 80 and over, reduce clinic blood pressure to below 150/90 mmHg.",
    evidence: [{ quote: "reduce clinic blood pressure to below 150/90 mmHg", chunk_id: "nice_ng136-p016-beee1ff3" }],
    citations: [{ document_name: "NICE NG136", section_title: "Monitoring treatment and blood pressure targets", page_number: 16, chunk_id: "nice_ng136-p016-beee1ff3" }],
    confidence: "High",
    disclaimer: "This information is derived from WHO and NICE hypertension guidelines and is intended for general clinical decision support only.",
  },
  timings_ms: { gate: 1.2, retrieval: 800, generation: 4000, audit: 1500 },
};

export const REFUSE_TRACE: AnswerTrace = {
  query: "What's the weather today?",
  gate: { verdict: "REFUSE", reason: "This system covers hypertension guidelines only.", triggered_by: "out_of_domain" },
  retrieval: null,
  threshold: null,
  raw_answer: null,
  audit: null,
  final: {
    recommendation: "This system covers hypertension guidelines only.",
    evidence: [],
    citations: [],
    confidence: "Insufficient Evidence",
    disclaimer: "Consult a healthcare provider.",
  },
  timings_ms: { gate: 0.5 },
};

export const HALT_TRACE: AnswerTrace = {
  query: "obscure question",
  gate: { verdict: "ALLOW", reason: "in scope", triggered_by: null },
  retrieval: {
    query: "obscure question",
    mode: "hybrid_rerank",
    k: 5,
    results: [
      {
        chunk: {
          text: "Some tangential chunk text.",
          metadata: {
            document_name: "NICE NG136",
            page_number: 3,
            section_title: "Background",
            chunk_id: "nice_ng136-p003-zzzz9999",
            source_url: "https://nice.org.uk/ng136",
            doc_key: "nice_ng136",
            section_path: ["Background"],
            page_end: null,
            token_count: 80,
            recommendation_ids: [],
            has_cross_reference: false,
            printed_page: null,
          },
        },
        score: 0.1,
        source: "hybrid_rerank",
      },
    ],
  },
  threshold: { action: "HALT", top_score: 0.1, reason: "Top retrieval score is below the halt threshold." },
  raw_answer: null,
  audit: null,
  final: {
    recommendation: "The guidelines do not contain enough relevant information to answer this question.",
    evidence: [],
    citations: [],
    confidence: "Insufficient Evidence",
    disclaimer: "Consult a healthcare provider.",
  },
  timings_ms: { gate: 0.5, retrieval: 900 },
};

export const RETRIEVAL_EVAL_REPORT: RetrievalEvalReport = {
  report_path: "/tmp/retrieval_report.json",
  timestamp: "2026-08-12T00:00:00+00:00",
  golden_set_size: 25,
  matrix: [
    { mode: "hybrid_rerank", k: 5, precision_at_k: 0.222, recall_at_k: 0.889, mrr: 0.769, n_questions_scored: 18 },
    { mode: "semantic", k: 5, precision_at_k: 0.178, recall_at_k: 0.722, mrr: 0.557, n_questions_scored: 18 },
  ],
  score_distributions: {
    hybrid_rerank: { answerable_top_scores: [0.9], out_of_scope_top_scores: [0.08], insufficient_top_scores: [0.52] },
    semantic: { answerable_top_scores: [0.7], out_of_scope_top_scores: [0.2], insufficient_top_scores: [0.4] },
    bm25: { answerable_top_scores: [12], out_of_scope_top_scores: [1], insufficient_top_scores: [3] },
    hybrid: { answerable_top_scores: [1], out_of_scope_top_scores: [1], insufficient_top_scores: [1] },
  },
};

export const E2E_EVAL_REPORT: E2EEvalReport = {
  report_path: "/tmp/e2e_report.json",
  timestamp: "2026-08-12T00:05:00+00:00",
  golden_set_size: 25,
  mode: "hybrid_rerank",
  k: 5,
  precision_at_k: 0.222,
  recall_at_k: 0.889,
  mrr: 0.769,
  n_questions_scored: 18,
  citation_accuracy: 1.0,
  unsupported_claim_rate: 0.0,
  refusal_correctness: 1.0,
  category_breakdown: {
    direct: { count: 10, correct: 10 },
    multi_chunk: { count: 4, correct: 4 },
    ambiguous: { count: 5, correct: 5 },
    out_of_scope: { count: 6, correct: 6 },
  },
  failures: [],
};

export const INGEST_RESPONSE: IngestResponse = {
  results: [
    { doc_key: "who_hypertension", chunk_count: 76, indexed_vector_count: 76, pages_path: "who_pages.jsonl", chunks_path: "who_chunks.jsonl" },
    { doc_key: "nice_ng136", chunk_count: 44, indexed_vector_count: 44, pages_path: "nice_pages.jsonl", chunks_path: "nice_chunks.jsonl" },
  ],
};

const SEARCH_RESULT: RetrievalResult = ALLOW_HIGH_TRACE.retrieval as RetrievalResult;

export const handlers = [
  http.get("http://localhost:8000/", () => HttpResponse.json({ app: "Wiqaya", status: "ok" })),
  http.post(`${API_BASE}/nlp/answer`, () => HttpResponse.json(ALLOW_HIGH_TRACE)),
  http.post(`${API_BASE}/nlp/search`, () => HttpResponse.json(SEARCH_RESULT)),
  http.post(`${API_BASE}/data/ingest`, () => HttpResponse.json(INGEST_RESPONSE)),
  http.post(`${API_BASE}/evaluation/retrieval`, () => HttpResponse.json(RETRIEVAL_EVAL_REPORT)),
  http.get(`${API_BASE}/evaluation/retrieval/latest`, () =>
    HttpResponse.json({ detail: "No saved retrieval evaluation yet — run one first." }, { status: 404 }),
  ),
  http.get(`${API_BASE}/evaluation/e2e/latest`, () =>
    HttpResponse.json({ detail: "No saved e2e evaluation yet — run one first." }, { status: 404 }),
  ),
  http.post(`${API_BASE}/evaluation/e2e`, () => HttpResponse.json(E2E_EVAL_REPORT)),
];
