from langchain_cohere import CohereRerank

from src.stores.reranker_factory import get_reranker
from tests.conftest import make_settings


class TestGetReranker:
    def test_cohere_backend_returns_cohere_rerank_with_configured_model(self):
        settings = make_settings(RERANKER_BACKEND="cohere", RERANKER_MODEL_ID="rerank-v3.5")
        reranker = get_reranker(settings)
        assert isinstance(reranker, CohereRerank)
        assert reranker.model == "rerank-v3.5"

    def test_top_n_override_is_applied(self):
        settings = make_settings(RERANKER_BACKEND="cohere")
        reranker = get_reranker(settings, top_n=7)
        assert reranker.top_n == 7

    def test_top_n_defaults_when_not_overridden(self):
        settings = make_settings(RERANKER_BACKEND="cohere")
        reranker = get_reranker(settings)
        assert reranker.top_n == 3
