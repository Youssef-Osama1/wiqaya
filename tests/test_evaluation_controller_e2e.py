from src.controllers.EvaluationController import EvaluationController
from src.core.schemas import (
    AnswerTrace,
    Chunk,
    ChunkMetadata,
    ClaimAudit,
    Citation,
    FinalAnswer,
    GateDecision,
    GoldenQuestion,
    QuoteCheck,
    RetrievalResult,
    ScoredChunk,
    ThresholdDecision,
)


def make_chunk(chunk_id: str) -> Chunk:
    return Chunk(
        text="t",
        metadata=ChunkMetadata(
            document_name="Doc", page_number=1, section_title="Sec", chunk_id=chunk_id,
            source_url="https://example.com", doc_key="doc", token_count=5,
        ),
    )


def make_scored(chunk_id: str, score: float) -> ScoredChunk:
    return ScoredChunk(chunk=make_chunk(chunk_id), score=score, source="hybrid_rerank")


def answered_trace(query, chunk_ids, confidence="High", verified=True):
    results = [make_scored(cid, 0.9) for cid in chunk_ids]
    quote_checks = [QuoteCheck(chunk_id=cid, quote="q", verified=verified, match_ratio=1.0 if verified else 0.1) for cid in chunk_ids]
    return AnswerTrace(
        query=query,
        gate=GateDecision(verdict="ALLOW", reason="in scope", triggered_by=None),
        retrieval=RetrievalResult(query=query, mode="hybrid_rerank", k=len(chunk_ids), results=results),
        threshold=ThresholdDecision(action="PROCEED", top_score=0.9, reason="ok"),
        raw_answer=None,
        audit=ClaimAudit(quote_checks=quote_checks, claims=[], unsupported_rate=0.0 if verified else 1.0),
        final=FinalAnswer(
            recommendation="rec",
            evidence=[],
            citations=[Citation(document_name="Doc", section_title="Sec", page_number=1, chunk_id=cid) for cid in chunk_ids],
            confidence=confidence,
            disclaimer="d",
        ),
        timings_ms={},
    )


def refused_trace(query):
    return AnswerTrace(
        query=query,
        gate=GateDecision(verdict="REFUSE", reason="out of scope", triggered_by="out_of_domain"),
        retrieval=None, threshold=None, raw_answer=None, audit=None,
        final=FinalAnswer(recommendation="refused", evidence=[], citations=[], confidence="Insufficient Evidence", disclaimer="d"),
        timings_ms={},
    )


def halted_trace(query):
    return AnswerTrace(
        query=query,
        gate=GateDecision(verdict="ALLOW", reason="in scope", triggered_by=None),
        retrieval=RetrievalResult(query=query, mode="hybrid_rerank", k=1, results=[make_scored("x", 0.1)]),
        threshold=ThresholdDecision(action="HALT", top_score=0.1, reason="too low"),
        raw_answer=None, audit=None,
        final=FinalAnswer(recommendation="insufficient", evidence=[], citations=[], confidence="Insufficient Evidence", disclaimer="d"),
        timings_ms={},
    )


class FakeAnswerer:
    def __init__(self, traces_by_query: dict[str, AnswerTrace]):
        self.traces_by_query = traces_by_query

    def answer(self, query: str, mode: str, k: int) -> AnswerTrace:
        return self.traces_by_query[query]


class FlakyAnswerer:
    def __init__(self, traces_by_query: dict[str, AnswerTrace], failing_query: str):
        self.traces_by_query = traces_by_query
        self.failing_query = failing_query

    def answer(self, query: str, mode: str, k: int) -> AnswerTrace:
        if query == self.failing_query:
            raise RuntimeError("simulated Cohere outage")
        return self.traces_by_query[query]


class TestEvaluateE2E:
    def test_answerable_question_scores_retrieval_metrics(self):
        golden = [GoldenQuestion(qid="D1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer")]
        answerer = FakeAnswerer({"q1": answered_trace("q1", ["a"])})
        report = EvaluationController(answerer).evaluate_e2e(golden, mode="hybrid_rerank", k=5)
        assert report["precision_at_k"] == 1.0
        assert report["recall_at_k"] == 1.0
        assert report["mrr"] == 1.0
        assert report["n_questions_scored"] == 1

    def test_verified_evidence_gives_perfect_citation_accuracy(self):
        golden = [GoldenQuestion(qid="D1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer")]
        answerer = FakeAnswerer({"q1": answered_trace("q1", ["a"], verified=True)})
        report = EvaluationController(answerer).evaluate_e2e(golden, mode="hybrid_rerank", k=5)
        assert report["citation_accuracy"] == 1.0
        assert report["unsupported_claim_rate"] == 0.0

    def test_hallucinated_quote_drops_citation_accuracy_and_raises_unsupported_rate(self):
        golden = [GoldenQuestion(qid="D1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer")]
        answerer = FakeAnswerer({"q1": answered_trace("q1", ["a"], verified=False)})
        report = EvaluationController(answerer).evaluate_e2e(golden, mode="hybrid_rerank", k=5)
        assert report["citation_accuracy"] == 0.0
        assert report["unsupported_claim_rate"] == 1.0

    def test_correctly_refused_out_of_scope_question_scores_perfect_refusal_correctness(self):
        golden = [GoldenQuestion(qid="O1", question="o1", category="out_of_scope", relevant_chunk_ids=[], expected_behavior="refuse")]
        answerer = FakeAnswerer({"o1": refused_trace("o1")})
        report = EvaluationController(answerer).evaluate_e2e(golden, mode="hybrid_rerank", k=5)
        assert report["refusal_correctness"] == 1.0
        assert report["failures"] == []

    def test_out_of_scope_question_that_was_answered_is_a_failure(self):
        golden = [GoldenQuestion(qid="O1", question="o1", category="out_of_scope", relevant_chunk_ids=[], expected_behavior="refuse")]
        answerer = FakeAnswerer({"o1": answered_trace("o1", ["x"])})
        report = EvaluationController(answerer).evaluate_e2e(golden, mode="hybrid_rerank", k=5)
        assert report["refusal_correctness"] == 0.0
        assert len(report["failures"]) == 1
        assert report["failures"][0]["qid"] == "O1"

    def test_halted_answerable_question_is_a_failure(self):
        golden = [GoldenQuestion(qid="D1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer")]
        answerer = FakeAnswerer({"q1": halted_trace("q1")})
        report = EvaluationController(answerer).evaluate_e2e(golden, mode="hybrid_rerank", k=5)
        assert len(report["failures"]) == 1
        assert report["failures"][0]["qid"] == "D1"

    def test_insufficient_expected_question_correct_when_halted(self):
        golden = [GoldenQuestion(qid="A3", question="a3", category="ambiguous", relevant_chunk_ids=[], expected_behavior="insufficient")]
        answerer = FakeAnswerer({"a3": halted_trace("a3")})
        report = EvaluationController(answerer).evaluate_e2e(golden, mode="hybrid_rerank", k=5)
        assert report["failures"] == []

    def test_category_breakdown_counts_correct_and_total_per_category(self):
        golden = [
            GoldenQuestion(qid="D1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer"),
            GoldenQuestion(qid="D2", question="q2", category="direct", relevant_chunk_ids=["b"], expected_behavior="answer"),
        ]
        answerer = FakeAnswerer({"q1": answered_trace("q1", ["a"]), "q2": halted_trace("q2")})
        report = EvaluationController(answerer).evaluate_e2e(golden, mode="hybrid_rerank", k=5)
        assert report["category_breakdown"]["direct"] == {"count": 2, "correct": 1}

    def test_golden_set_size_reflects_all_questions_not_just_scored(self):
        golden = [
            GoldenQuestion(qid="D1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer"),
            GoldenQuestion(qid="O1", question="o1", category="out_of_scope", relevant_chunk_ids=[], expected_behavior="refuse"),
        ]
        answerer = FakeAnswerer({"q1": answered_trace("q1", ["a"]), "o1": refused_trace("o1")})
        report = EvaluationController(answerer).evaluate_e2e(golden, mode="hybrid_rerank", k=5)
        assert report["golden_set_size"] == 2
        assert report["n_questions_scored"] == 1

    def test_one_question_erroring_does_not_abort_the_whole_batch(self):
        golden = [
            GoldenQuestion(qid="D1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer"),
            GoldenQuestion(qid="D2", question="q2", category="direct", relevant_chunk_ids=["b"], expected_behavior="answer"),
            GoldenQuestion(qid="D3", question="q3", category="direct", relevant_chunk_ids=["c"], expected_behavior="answer"),
        ]
        answerer = FlakyAnswerer(
            {"q1": answered_trace("q1", ["a"]), "q3": answered_trace("q3", ["c"])},
            failing_query="q2",
        )
        report = EvaluationController(answerer).evaluate_e2e(golden, mode="hybrid_rerank", k=5)

        assert report["n_questions_scored"] == 2
        assert report["precision_at_k"] == 1.0

        errored = [f for f in report["failures"] if f["qid"] == "D2"]
        assert len(errored) == 1
        assert "simulated Cohere outage" in errored[0]["error"]
        assert report["category_breakdown"]["direct"] == {"count": 3, "correct": 2}
