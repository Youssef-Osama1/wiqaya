from datetime import datetime, timezone
from typing import Protocol

from src.core.evaluation.metrics import (
    citation_accuracy,
    precision_at_k,
    reciprocal_rank,
    recall_at_k,
    refusal_correctness,
    unsupported_claim_rate,
)
from src.core.schemas import AnswerTrace, GoldenQuestion, RetrievalResult


class Searcher(Protocol):
    def search(self, query: str, mode: str, k: int) -> RetrievalResult: ...


class Answerer(Protocol):
    def answer(self, query: str, mode: str, k: int) -> AnswerTrace: ...


class EvaluationController:
    def __init__(self, client: Searcher | Answerer):
        self.searcher = client
        self.answerer = client

    def evaluate_retrieval(self, golden_questions: list[GoldenQuestion], modes: list[str], ks: list[int]) -> dict:
        scored_questions = [q for q in golden_questions if q.relevant_chunk_ids]
        matrix = []
        score_distributions: dict[str, dict[str, list[float]]] = {}

        for mode in modes:
            answerable_scores: list[float] = []
            out_of_scope_scores: list[float] = []
            insufficient_scores: list[float] = []
            max_k = max(ks)

            results_by_qid = {q.qid: self._safe_search(q, mode, max_k) for q in golden_questions}

            for q in golden_questions:
                top_score = results_by_qid[q.qid].results[0].score if results_by_qid[q.qid].results else 0.0
                if q.relevant_chunk_ids:
                    answerable_scores.append(top_score)
                elif q.expected_behavior == "refuse":
                    out_of_scope_scores.append(top_score)
                elif q.expected_behavior == "insufficient":
                    insufficient_scores.append(top_score)

            score_distributions[mode] = {
                "answerable_top_scores": answerable_scores,
                "out_of_scope_top_scores": out_of_scope_scores,
                "insufficient_top_scores": insufficient_scores,
            }

            for k in ks:
                precisions, recalls, rrs = [], [], []
                for q in scored_questions:
                    retrieved_ids = [sc.chunk.metadata.chunk_id for sc in results_by_qid[q.qid].results[:k]]
                    relevant = set(q.relevant_chunk_ids)
                    precisions.append(precision_at_k(retrieved_ids, relevant, k))
                    recalls.append(recall_at_k(retrieved_ids, relevant, k))
                    rrs.append(reciprocal_rank(retrieved_ids, relevant))

                n = len(scored_questions)
                matrix.append(
                    {
                        "mode": mode,
                        "k": k,
                        "precision_at_k": sum(precisions) / n if n else 0.0,
                        "recall_at_k": sum(recalls) / n if n else 0.0,
                        "mrr": sum(rrs) / n if n else 0.0,
                        "n_questions_scored": n,
                    }
                )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "golden_set_size": len(golden_questions),
            "matrix": matrix,
            "score_distributions": score_distributions,
        }

    def evaluate_e2e(self, golden_questions: list[GoldenQuestion], mode: str, k: int) -> dict:
        precisions, recalls, rrs = [], [], []
        quote_checks_pool = []
        claim_audits_pool = []
        refused_flags = []
        category_counts: dict[str, int] = {}
        category_correct: dict[str, int] = {}
        failures = []

        for q in golden_questions:
            try:
                trace = self.answerer.answer(q.question, mode, k)
            except Exception as e:
                category_counts[q.category] = category_counts.get(q.category, 0) + 1
                failures.append(
                    {
                        "qid": q.qid,
                        "question": q.question,
                        "category": q.category,
                        "expected_behavior": q.expected_behavior,
                        "actual_gate_verdict": None,
                        "actual_confidence": None,
                        "relevant_chunk_ids": q.relevant_chunk_ids,
                        "retrieved_chunk_ids": [],
                        "error": str(e),
                    }
                )
                continue

            retrieved_ids = [sc.chunk.metadata.chunk_id for sc in trace.retrieval.results] if trace.retrieval else []

            if q.relevant_chunk_ids:
                relevant = set(q.relevant_chunk_ids)
                precisions.append(precision_at_k(retrieved_ids, relevant, k))
                recalls.append(recall_at_k(retrieved_ids, relevant, k))
                rrs.append(reciprocal_rank(retrieved_ids, relevant))

            if trace.audit:
                quote_checks_pool.extend(trace.audit.quote_checks)
                claim_audits_pool.append(trace.audit)

            if q.expected_behavior == "refuse":
                refused_flags.append(trace.gate.verdict == "REFUSE")

            category_counts[q.category] = category_counts.get(q.category, 0) + 1
            correct = self._behavior_correct(q.expected_behavior, trace)
            category_correct[q.category] = category_correct.get(q.category, 0) + (1 if correct else 0)

            if not correct:
                failures.append(
                    {
                        "qid": q.qid,
                        "question": q.question,
                        "category": q.category,
                        "expected_behavior": q.expected_behavior,
                        "actual_gate_verdict": trace.gate.verdict,
                        "actual_confidence": trace.final.confidence,
                        "relevant_chunk_ids": q.relevant_chunk_ids,
                        "retrieved_chunk_ids": retrieved_ids[:k],
                    }
                )

        n = len(precisions)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "golden_set_size": len(golden_questions),
            "mode": mode,
            "k": k,
            "precision_at_k": sum(precisions) / n if n else 0.0,
            "recall_at_k": sum(recalls) / n if n else 0.0,
            "mrr": sum(rrs) / n if n else 0.0,
            "n_questions_scored": n,
            "citation_accuracy": citation_accuracy(quote_checks_pool),
            "unsupported_claim_rate": unsupported_claim_rate(claim_audits_pool),
            "refusal_correctness": refusal_correctness(refused_flags),
            "category_breakdown": {
                cat: {"count": category_counts[cat], "correct": category_correct[cat]} for cat in category_counts
            },
            "failures": failures,
        }

    def _safe_search(self, question: GoldenQuestion, mode: str, k: int) -> RetrievalResult:
        try:
            return self.searcher.search(question.question, mode, k)
        except Exception:
            return RetrievalResult(query=question.question, mode=mode, k=k, results=[])

    @staticmethod
    def _behavior_correct(expected_behavior: str, trace: AnswerTrace) -> bool:
        if expected_behavior == "refuse":
            return trace.gate.verdict == "REFUSE"
        if expected_behavior == "insufficient":
            return trace.final.confidence == "Insufficient Evidence"
        return trace.gate.verdict != "REFUSE" and trace.final.confidence != "Insufficient Evidence"
