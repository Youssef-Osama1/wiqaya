import uuid

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.helpers.config import get_settings
from src.main import app

FAKE_EMBEDDINGS = DeterministicFakeEmbedding(size=32)


class ReversingFakeReranker(BaseDocumentCompressor):
    def compress_documents(self, documents, query, callbacks=None):
        reversed_docs = list(reversed(documents))
        for i, doc in enumerate(reversed_docs):
            doc.metadata["relevance_score"] = 1.0 - (i / max(len(reversed_docs), 1))
        return reversed_docs


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
    test_collection_name = f"wiqaya_nlp_route_test_{uuid.uuid4().hex[:8]}"
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


@pytest.fixture
def client():
    with TestClient(app) as c:
        c.post("/api/v1/data/ingest", json={"doc_keys": ["nice_ng136"]})
        yield c


class TestSearchRoute:
    @pytest.mark.parametrize("mode", ["semantic", "bm25", "hybrid", "hybrid_rerank"])
    def test_every_mode_returns_results_with_full_metadata(self, client, mode):
        response = client.post("/api/v1/nlp/search", json={"query": "blood pressure treatment", "mode": mode, "k": 3})
        assert response.status_code == 200
        body = response.json()
        assert body["mode"] == mode
        assert body["results"]
        for scored in body["results"]:
            assert scored["source"] == mode
            meta = scored["chunk"]["metadata"]
            assert meta["chunk_id"]
            assert meta["document_name"]
            assert meta["page_number"] > 0
            assert meta["source_url"]

    def test_bm25_mode_returns_nonempty_results(self, client):
        response = client.post("/api/v1/nlp/search", json={"query": "hypertension", "mode": "bm25"})
        assert response.status_code == 200
        assert len(response.json()["results"]) > 0

    def test_rerank_mode_reorders_relative_to_hybrid(self, client):
        hybrid = client.post("/api/v1/nlp/search", json={"query": "hypertension treatment", "mode": "hybrid", "k": 5}).json()
        reranked = client.post(
            "/api/v1/nlp/search", json={"query": "hypertension treatment", "mode": "hybrid_rerank", "k": 5}
        ).json()
        hybrid_order = [r["chunk"]["metadata"]["chunk_id"] for r in hybrid["results"]]
        reranked_order = [r["chunk"]["metadata"]["chunk_id"] for r in reranked["results"]]
        assert reranked_order != hybrid_order

    def test_default_k_comes_from_settings(self, client):
        response = client.post("/api/v1/nlp/search", json={"query": "hypertension", "mode": "bm25"})
        assert response.json()["k"] == get_settings().DEFAULT_TOP_K

    def test_search_before_ingest_returns_503(self, monkeypatch):
        settings = get_settings()
        original_collection = settings.VECTOR_COLLECTION_NAME
        settings.VECTOR_COLLECTION_NAME = f"wiqaya_never_ingested_{uuid.uuid4().hex[:8]}"
        try:
            with TestClient(app) as c:
                response = c.post("/api/v1/nlp/search", json={"query": "hypertension", "mode": "semantic"})
                assert response.status_code == 503
        finally:
            settings.VECTOR_COLLECTION_NAME = original_collection
