import time
from typing import Optional, Protocol

from langchain_core.language_models.chat_models import BaseChatModel

from src.core.generation.chain import generate_grounded_answer
from src.core.generation.citations import resolve_citations
from src.core.generation.confidence import compute_confidence
from src.core.generation.context import assemble_context
from src.core.guardrails.claim_audit import compute_claim_audit
from src.core.guardrails.claim_extraction import extract_claim_support
from src.core.guardrails.claim_verification import verify_evidence_quote
from src.core.guardrails.thresholds import evaluate_threshold
from src.core.schemas import AnswerTrace, FinalAnswer, GateDecision, RetrievalMode, RetrievalResult
from src.helpers.config import Settings

DISCLAIMER = (
    "This information is derived from WHO and NICE hypertension guidelines and is intended "
    "for general clinical decision support only. It is not a substitute for professional "
    "medical judgment — always consult a qualified healthcare provider for decisions about "
    "individual patient care."
)

CAUTION_DISCLAIMER = (
    DISCLAIMER + " This question appears to ask for personal medical advice — please consult "
    "a healthcare provider directly rather than relying on this general guideline summary."
)


class GateEvaluator(Protocol):
    def evaluate(self, query: str) -> GateDecision: ...


class Retriever(Protocol):
    def search(self, query: str, mode: str, k: int) -> RetrievalResult: ...


class AnswerController:
    def __init__(self, settings: Settings, gate_controller: GateEvaluator, retrieval_controller: Retriever, llm: BaseChatModel):
        self.settings = settings
        self.gate_controller = gate_controller
        self.retrieval_controller = retrieval_controller
        self.llm = llm

    def answer(self, query: str, mode: RetrievalMode = "hybrid_rerank", k: Optional[int] = None) -> AnswerTrace:
        timings_ms: dict[str, float] = {}

        gate = self._timed(timings_ms, "gate", lambda: self.gate_controller.evaluate(query))

        if gate.verdict == "REFUSE":
            final = FinalAnswer(recommendation=gate.reason, evidence=[], citations=[], confidence="Insufficient Evidence", disclaimer=DISCLAIMER)
            return AnswerTrace(query=query, gate=gate, retrieval=None, threshold=None, raw_answer=None, audit=None, final=final, timings_ms=timings_ms)

        k = k or self.settings.DEFAULT_TOP_K
        retrieval = self._timed(timings_ms, "retrieval", lambda: self.retrieval_controller.search(query, mode, k))
        threshold = evaluate_threshold(retrieval, self.settings.SIM_HALT_THRESHOLD, self.settings.SIM_DOWNGRADE_THRESHOLD)

        if threshold.action == "HALT":
            final = FinalAnswer(
                recommendation="The guidelines do not contain enough relevant information to answer this question.",
                evidence=[], citations=[], confidence="Insufficient Evidence", disclaimer=DISCLAIMER,
            )
            return AnswerTrace(query=query, gate=gate, retrieval=retrieval, threshold=threshold, raw_answer=None, audit=None, final=final, timings_ms=timings_ms)

        chunks = [scored.chunk for scored in retrieval.results]
        raw_answer = self._timed(timings_ms, "generation", lambda: generate_grounded_answer(self.llm, query, chunks))

        chunks_by_id = {chunk.metadata.chunk_id: chunk for chunk in chunks}

        def run_audit():
            quote_checks = [
                verify_evidence_quote(item, chunks_by_id[item.chunk_id].text)
                for item in raw_answer.evidence
                if item.chunk_id in chunks_by_id
            ]
            claims = extract_claim_support(self.llm, raw_answer.recommendation, assemble_context(chunks))
            return compute_claim_audit(quote_checks, claims)

        audit = self._timed(timings_ms, "audit", run_audit)

        verified_chunk_ids = {qc.chunk_id for qc in audit.quote_checks if qc.verified}
        final_evidence = [item for item in raw_answer.evidence if item.chunk_id in verified_chunk_ids]
        citations, _unresolved_chunk_ids = resolve_citations(final_evidence, chunks)

        confidence = compute_confidence(gate, threshold, audit, raw_answer)
        disclaimer = CAUTION_DISCLAIMER if gate.verdict == "CAUTION" else DISCLAIMER

        final = FinalAnswer(recommendation=raw_answer.recommendation, evidence=final_evidence, citations=citations, confidence=confidence, disclaimer=disclaimer)

        return AnswerTrace(query=query, gate=gate, retrieval=retrieval, threshold=threshold, raw_answer=raw_answer, audit=audit, final=final, timings_ms=timings_ms)

    @staticmethod
    def _timed(timings_ms: dict[str, float], key: str, fn):
        start = time.perf_counter()
        result = fn()
        timings_ms[key] = (time.perf_counter() - start) * 1000
        return result
