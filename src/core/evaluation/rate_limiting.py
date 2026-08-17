import time

from src.core.schemas import AnswerTrace, RetrievalMode, RetrievalResult


class RateLimitedSearcher:
    def __init__(self, inner, delay: float):
        self.inner = inner
        self.delay = delay

    def search(self, query: str, mode: RetrievalMode, k: int) -> RetrievalResult:
        result = self.inner.search(query, mode, k)
        if mode != "bm25" and self.delay:
            time.sleep(self.delay)
        return result


class RateLimitedAnswerer:
    def __init__(self, inner, delay: float):
        self.inner = inner
        self.delay = delay

    def answer(self, query: str, mode: RetrievalMode, k: int) -> AnswerTrace:
        result = self.inner.answer(query, mode, k)
        if self.delay:
            time.sleep(self.delay)
        return result
