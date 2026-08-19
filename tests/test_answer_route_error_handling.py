import uuid

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.core.guardrails.gate_classifier import ClassifierVerdict
from src.helpers.config import get_settings
from src.main import app

FAKE_EMBEDDINGS = DeterministicFakeEmbedding(size=32)


class ReversingFakeReranker(BaseDocumentCompressor):
    def compress_documents(self, documents, query, callbacks=None):
        reversed_docs = list(reversed(documents))
        for i, doc in enumerate(reversed_docs):
            doc.metadata["relevance_score"] = 1.0 - (i / max(len(reversed_docs), 1))
        return reversed_docs


class FailingStructuredRunnable:
    def invoke(self, _messages):
        raise RuntimeError("simulated Cohere outage (502 from upstream)")


class FlakyLlm:
    def with_structured_output(self, schema):
        if schema is ClassifierVerdict:
            from tests.test_answer_route import FakeStructuredRunnable

            return FakeStructuredRunnable(ClassifierVerdict(verdict="ALLOW", reason="in-scope"))
        return FailingStructuredRunnable()


@pytest.fixture(autouse=True)
def fake_embeddings_and_isolated_collection(monkeypatch):
    monkeypatch.setattr("src.controllers.IngestionController.get_embeddings", lambda settings: FAKE_EMBEDDINGS)
    monkeypatch.setattr("src.main.get_embeddings", lambda settings: FAKE_EMBEDDINGS)
    monkeypatch.setattr(
        "src.controllers.RetrievalController.get_reranker",
        lambda settings, top_n=None: ReversingFakeReranker(),
    )

    settings = get_settings()
    original_collection = settings.VECTOR_COLLECTION_NAME
    test_collection_name = f"wiqaya_error_route_test_{uuid.uuid4().hex[:8]}"
    settings.VECTOR_COLLECTION_NAME = test_collection_name
    yield
    settings.VECTOR_COLLECTION_NAME = original_collection

    import psycopg
    from qdrant_client import QdrantClient

    with psycopg.connect(
        f"host={settings.POSTGRES_HOST} port={settings.POSTGRES_PORT} "
        f"user={settings.POSTGRES_USER} password={settings.POSTGRES_PASSWORD} dbname={settings.POSTGRES_DB}"
    ) as conn:
        conn.execute("DELETE FROM langchain_pg_embedding WHERE id LIKE 'nice_ng136-%'")
        conn.commit()
    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    if client.collection_exists(test_collection_name):
        client.delete_collection(test_collection_name)


class TestAnswerRouteErrorHandling:
    def test_llm_failure_during_generation_returns_clean_502_not_a_raw_crash(self):
        with TestClient(app, raise_server_exceptions=False) as c:
            c.post("/api/v1/data/ingest", json={"doc_keys": ["nice_ng136"]})
            c.app.state.llm = FlakyLlm()

            response = c.post("/api/v1/nlp/answer", json={"query": "What is the first-line treatment?"})

        assert response.status_code == 502
        body = response.json()
        assert "detail" in body
        assert "internal server error" not in body["detail"].lower()
