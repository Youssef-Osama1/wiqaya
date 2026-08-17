from src.controllers.EvaluationController import EvaluationController
from src.core.schemas import Chunk, ChunkMetadata, GoldenAnchor, GoldenQuestion, RetrievalResult, ScoredChunk


def make_chunk_metadata(chunk_id: str) -> ChunkMetadata:
    return ChunkMetadata(
        document_name="Doc", page_number=1, section_title="Sec", chunk_id=chunk_id,
        source_url="https://example.com", doc_key="doc", token_count=5,
    )


def make_scored(chunk_id: str, score: float) -> ScoredChunk:
    return ScoredChunk(chunk=Chunk(text="t", metadata=make_chunk_metadata(chunk_id)), score=score, source="semantic")


class FakeSearcher:
    def __init__(self, results_by_query: dict[str, list[ScoredChunk]]):
        self.results_by_query = results_by_query

    def search(self, query: str, mode: str, k: int) -> RetrievalResult:
        results = self.results_by_query.get(query, [])[:k]
        return RetrievalResult(query=query, mode=mode, k=k, results=results)


class FlakySearcher:
    """Raises for one specific query (simulating a rate-limit hit mid-run),
    answers normally for everything else."""

    def __init__(self, results_by_query: dict[str, list[ScoredChunk]], failing_query: str):
        self.results_by_query = results_by_query
        self.failing_query = failing_query

    def search(self, query: str, mode: str, k: int) -> RetrievalResult:
        if query == self.failing_query:
            raise RuntimeError("simulated Cohere rate limit (429)")
        results = self.results_by_query.get(query, [])[:k]
        return RetrievalResult(query=query, mode=mode, k=k, results=results)


class TestEvaluateRetrieval:
    def test_perfect_retrieval_gives_precision_recall_mrr_of_one(self):
        golden = [GoldenQuestion(qid="Q1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer")]
        searcher = FakeSearcher({"q1": [make_scored("a", 0.9)]})
        controller = EvaluationController(searcher)
        report = controller.evaluate_retrieval(golden, modes=["semantic"], ks=[3])
        row = report["matrix"][0]
        assert row["precision_at_k"] == 1.0
        assert row["recall_at_k"] == 1.0
        assert row["mrr"] == 1.0
        assert row["n_questions_scored"] == 1

    def test_out_of_scope_questions_excluded_from_precision_recall_mrr(self):
        golden = [
            GoldenQuestion(qid="Q1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer"),
            GoldenQuestion(qid="O1", question="o1", category="out_of_scope", relevant_chunk_ids=[], expected_behavior="refuse"),
        ]
        searcher = FakeSearcher({"q1": [make_scored("a", 0.9)], "o1": [make_scored("x", 0.1)]})
        controller = EvaluationController(searcher)
        report = controller.evaluate_retrieval(golden, modes=["semantic"], ks=[3])
        assert report["matrix"][0]["n_questions_scored"] == 1

    def test_score_distributions_include_all_categories(self):
        golden = [
            GoldenQuestion(qid="Q1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer"),
            GoldenQuestion(qid="O1", question="o1", category="out_of_scope", relevant_chunk_ids=[], expected_behavior="refuse"),
        ]
        searcher = FakeSearcher({"q1": [make_scored("a", 0.9)], "o1": [make_scored("x", 0.15)]})
        controller = EvaluationController(searcher)
        report = controller.evaluate_retrieval(golden, modes=["semantic"], ks=[3])
        dist = report["score_distributions"]["semantic"]
        assert dist["answerable_top_scores"] == [0.9]
        assert dist["out_of_scope_top_scores"] == [0.15]

    def test_matrix_covers_every_mode_k_combination(self):
        golden = [GoldenQuestion(qid="Q1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer")]
        searcher = FakeSearcher({"q1": [make_scored("a", 0.9)]})
        controller = EvaluationController(searcher)
        report = controller.evaluate_retrieval(golden, modes=["semantic", "bm25"], ks=[3, 5])
        combos = {(row["mode"], row["k"]) for row in report["matrix"]}
        assert combos == {("semantic", 3), ("semantic", 5), ("bm25", 3), ("bm25", 5)}

    def test_partial_precision_when_only_some_retrieved_are_relevant(self):
        golden = [GoldenQuestion(qid="Q1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer")]
        searcher = FakeSearcher({"q1": [make_scored("x", 0.9), make_scored("a", 0.5), make_scored("y", 0.4)]})
        controller = EvaluationController(searcher)
        report = controller.evaluate_retrieval(golden, modes=["semantic"], ks=[3])
        row = report["matrix"][0]
        assert row["precision_at_k"] == 1 / 3
        assert row["recall_at_k"] == 1.0
        assert row["mrr"] == 1 / 2

    def test_multi_chunk_question_uses_all_relevant_ids(self):
        golden = [GoldenQuestion(qid="M1", question="m1", category="multi_chunk", relevant_chunk_ids=["a", "b"], expected_behavior="answer")]
        searcher = FakeSearcher({"m1": [make_scored("a", 0.9), make_scored("c", 0.6), make_scored("b", 0.5)]})
        controller = EvaluationController(searcher)
        report = controller.evaluate_retrieval(golden, modes=["semantic"], ks=[3])
        row = report["matrix"][0]
        assert row["recall_at_k"] == 1.0

    def test_one_question_raising_does_not_abort_the_whole_matrix(self):
        golden = [
            GoldenQuestion(qid="Q1", question="q1", category="direct", relevant_chunk_ids=["a"], expected_behavior="answer"),
            GoldenQuestion(qid="Q2", question="q2", category="direct", relevant_chunk_ids=["b"], expected_behavior="answer"),
        ]
        searcher = FlakySearcher({"q1": [make_scored("a", 0.9)], "q2": [make_scored("b", 0.9)]}, failing_query="q1")
        controller = EvaluationController(searcher)
        report = controller.evaluate_retrieval(golden, modes=["semantic"], ks=[3])
        row = report["matrix"][0]
        assert row["n_questions_scored"] == 2  # Q1 counted as a zero-result miss, not dropped
        assert row["recall_at_k"] == 0.5  # only Q2 scored a hit

    def test_failed_question_contributes_a_zero_score_not_a_crash(self):
        golden = [GoldenQuestion(qid="O1", question="o1", category="out_of_scope", relevant_chunk_ids=[], expected_behavior="refuse")]
        searcher = FlakySearcher({}, failing_query="o1")
        controller = EvaluationController(searcher)
        report = controller.evaluate_retrieval(golden, modes=["semantic"], ks=[3])
        assert report["score_distributions"]["semantic"]["out_of_scope_top_scores"] == [0.0]
