from unittest.mock import patch

from src.core.evaluation.rate_limiting import RateLimitedAnswerer, RateLimitedSearcher
from src.core.schemas import AnswerTrace, FinalAnswer, GateDecision, RetrievalResult


class FakeSearcher:
    def __init__(self):
        self.calls = []

    def search(self, query, mode, k):
        self.calls.append((query, mode, k))
        return RetrievalResult(query=query, mode=mode, k=k, results=[])


class FakeAnswerer:
    def __init__(self):
        self.calls = []

    def answer(self, query, mode, k):
        self.calls.append((query, mode, k))
        return AnswerTrace(
            query=query,
            gate=GateDecision(verdict="ALLOW", reason="r", triggered_by=None),
            retrieval=None, threshold=None, raw_answer=None, audit=None,
            final=FinalAnswer(recommendation="r", evidence=[], citations=[], confidence="High", disclaimer="d"),
            timings_ms={},
        )


class TestRateLimitedSearcher:
    def test_delegates_the_call_and_returns_the_real_result(self):
        inner = FakeSearcher()
        searcher = RateLimitedSearcher(inner, delay=0)
        result = searcher.search("q", "hybrid_rerank", 5)
        assert result.query == "q"
        assert inner.calls == [("q", "hybrid_rerank", 5)]

    def test_sleeps_between_calls_when_delay_is_set(self):
        inner = FakeSearcher()
        searcher = RateLimitedSearcher(inner, delay=2.5)
        with patch("src.core.evaluation.rate_limiting.time.sleep") as mock_sleep:
            searcher.search("q", "hybrid_rerank", 5)
        mock_sleep.assert_called_once_with(2.5)

    def test_does_not_sleep_for_bm25_since_it_makes_no_api_call(self):
        inner = FakeSearcher()
        searcher = RateLimitedSearcher(inner, delay=2.5)
        with patch("src.core.evaluation.rate_limiting.time.sleep") as mock_sleep:
            searcher.search("q", "bm25", 5)
        mock_sleep.assert_not_called()

    def test_zero_delay_never_sleeps(self):
        inner = FakeSearcher()
        searcher = RateLimitedSearcher(inner, delay=0)
        with patch("src.core.evaluation.rate_limiting.time.sleep") as mock_sleep:
            searcher.search("q", "hybrid_rerank", 5)
        mock_sleep.assert_not_called()


class TestRateLimitedAnswerer:
    def test_delegates_the_call_and_returns_the_real_trace(self):
        inner = FakeAnswerer()
        answerer = RateLimitedAnswerer(inner, delay=0)
        trace = answerer.answer("q", "hybrid_rerank", 5)
        assert trace.query == "q"
        assert inner.calls == [("q", "hybrid_rerank", 5)]

    def test_sleeps_after_every_call_when_delay_is_set(self):
        inner = FakeAnswerer()
        answerer = RateLimitedAnswerer(inner, delay=3.0)
        with patch("src.core.evaluation.rate_limiting.time.sleep") as mock_sleep:
            answerer.answer("q", "hybrid_rerank", 5)
        mock_sleep.assert_called_once_with(3.0)

    def test_zero_delay_never_sleeps(self):
        inner = FakeAnswerer()
        answerer = RateLimitedAnswerer(inner, delay=0)
        with patch("src.core.evaluation.rate_limiting.time.sleep") as mock_sleep:
            answerer.answer("q", "hybrid_rerank", 5)
        mock_sleep.assert_not_called()
