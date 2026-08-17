from src.core.guardrails.thresholds import evaluate_threshold
from src.core.schemas import Chunk, ChunkMetadata, RetrievalResult, ScoredChunk


def make_result(scores: list[float]) -> RetrievalResult:
    results = [
        ScoredChunk(
            chunk=Chunk(
                text="t",
                metadata=ChunkMetadata(
                    document_name="Doc", page_number=1, section_title="Sec",
                    chunk_id=f"c{i}", source_url="https://example.com", doc_key="doc", token_count=5,
                ),
            ),
            score=score,
            source="hybrid_rerank",
        )
        for i, score in enumerate(scores)
    ]
    return RetrievalResult(query="q", mode="hybrid_rerank", k=len(scores), results=results)


class TestEvaluateThreshold:
    def test_score_below_halt_threshold_halts(self):
        decision = evaluate_threshold(make_result([0.2]), halt_threshold=0.45, downgrade_threshold=0.65)
        assert decision.action == "HALT"
        assert decision.top_score == 0.2

    def test_score_between_halt_and_downgrade_downgrades(self):
        decision = evaluate_threshold(make_result([0.5]), halt_threshold=0.45, downgrade_threshold=0.65)
        assert decision.action == "DOWNGRADE"
        assert decision.top_score == 0.5

    def test_score_at_or_above_downgrade_threshold_proceeds(self):
        decision = evaluate_threshold(make_result([0.9]), halt_threshold=0.45, downgrade_threshold=0.65)
        assert decision.action == "PROCEED"

    def test_score_exactly_at_halt_threshold_does_not_halt(self):
        decision = evaluate_threshold(make_result([0.45]), halt_threshold=0.45, downgrade_threshold=0.65)
        assert decision.action == "DOWNGRADE"

    def test_score_exactly_at_downgrade_threshold_proceeds(self):
        decision = evaluate_threshold(make_result([0.65]), halt_threshold=0.45, downgrade_threshold=0.65)
        assert decision.action == "PROCEED"

    def test_no_results_halts_with_zero_score(self):
        decision = evaluate_threshold(make_result([]), halt_threshold=0.45, downgrade_threshold=0.65)
        assert decision.action == "HALT"
        assert decision.top_score == 0.0

    def test_uses_top_ranked_result_not_max_of_all(self):
        decision = evaluate_threshold(make_result([0.9, 0.99]), halt_threshold=0.45, downgrade_threshold=0.65)
        assert decision.top_score == 0.9
