import uuid

import pytest
from fastapi.testclient import TestClient
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.helpers.config import get_settings
from src.main import app

FAKE_EMBEDDINGS = DeterministicFakeEmbedding(size=32)


@pytest.fixture(autouse=True)
def fake_embeddings_and_isolated_collection(monkeypatch):
    monkeypatch.setattr("src.controllers.IngestionController.get_embeddings", lambda settings: FAKE_EMBEDDINGS)
    monkeypatch.setattr("src.main.get_embeddings", lambda settings: FAKE_EMBEDDINGS)

    settings = get_settings()
    original_collection = settings.VECTOR_COLLECTION_NAME
    test_collection_name = f"wiqaya_route_test_{uuid.uuid4().hex[:8]}"
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
        yield c


class TestIngestRoute:
    def test_ingest_single_doc_returns_matching_counts(self, client):
        response = client.post("/api/v1/data/ingest", json={"doc_keys": ["nice_ng136"]})
        assert response.status_code == 200
        body = response.json()
        assert len(body["results"]) == 1
        result = body["results"][0]
        assert result["doc_key"] == "nice_ng136"
        assert result["chunk_count"] > 0
        assert result["indexed_vector_count"] == result["chunk_count"]

    def test_unknown_doc_key_returns_404(self, client):
        response = client.post("/api/v1/data/ingest", json={"doc_keys": ["not_a_real_doc"]})
        assert response.status_code == 404

    def test_chunk_config_override_is_applied(self, client):
        response = client.post(
            "/api/v1/data/ingest",
            json={"doc_keys": ["nice_ng136"], "target_tokens": 300, "hard_max_tokens": 400},
        )
        assert response.status_code == 200
        default_response_count = client.post("/api/v1/data/ingest", json={"doc_keys": ["nice_ng136"]}).json()
        smaller_config_count = response.json()["results"][0]["chunk_count"]
        assert smaller_config_count >= default_response_count["results"][0]["chunk_count"]


class TestRootRoute:
    def test_root_returns_ok(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
