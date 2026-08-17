from langchain_cohere import CohereEmbeddings
from langchain_openai import OpenAIEmbeddings

from src.stores.embedding_factory import get_embeddings
from tests.conftest import make_settings


class TestGetEmbeddings:
    def test_openai_backend_returns_openai_embeddings_with_configured_model(self):
        settings = make_settings(EMBEDDING_BACKEND="openai", EMBEDDING_MODEL_ID="text-embedding-3-small")
        embeddings = get_embeddings(settings)
        assert isinstance(embeddings, OpenAIEmbeddings)
        assert embeddings.model == "text-embedding-3-small"

    def test_cohere_backend_returns_cohere_embeddings_with_configured_model(self):
        settings = make_settings(EMBEDDING_BACKEND="cohere", EMBEDDING_MODEL_ID="embed-english-v3.0")
        embeddings = get_embeddings(settings)
        assert isinstance(embeddings, CohereEmbeddings)
        assert embeddings.model == "embed-english-v3.0"
