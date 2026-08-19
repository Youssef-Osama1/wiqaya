import uuid

import pytest
from fastapi.testclient import TestClient
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.helpers.config import get_settings
from src.main import app

FAKE_EMBEDDINGS = DeterministicFakeEmbedding(size=32)


class TestCors:
    def test_allowed_origin_gets_cors_header_on_preflight(self):
        with TestClient(app) as c:
            response = c.options(
                "/api/v1/nlp/search",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_disallowed_origin_gets_no_cors_header(self):
        with TestClient(app) as c:
            response = c.options(
                "/api/v1/nlp/search",
                headers={
                    "Origin": "http://evil.example.com",
                    "Access-Control-Request-Method": "POST",
                },
            )
        assert "access-control-allow-origin" not in response.headers


class TestUnhandledExceptionStillCarriesCors:
    """An unhandled exception deep in a route (e.g. a Cohere rate-limit error) must
    still get a CORS header on its error response — otherwise the browser reports a
    generic network failure ("could not reach the API") instead of a readable error,
    even though the server is up and responded."""

    @pytest.fixture(autouse=True)
    def fake_embeddings_and_isolated_collection(self, monkeypatch):
        monkeypatch.setattr("src.controllers.IngestionController.get_embeddings", lambda settings: FAKE_EMBEDDINGS)
        monkeypatch.setattr("src.main.get_embeddings", lambda settings: FAKE_EMBEDDINGS)

        settings = get_settings()
        original_collection = settings.VECTOR_COLLECTION_NAME
        test_collection_name = f"wiqaya_cors_crash_test_{uuid.uuid4().hex[:8]}"
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

    def test_unhandled_exception_in_a_route_still_gets_cors_header(self, monkeypatch):
        def boom(self, query, mode, k):
            raise RuntimeError("simulated Cohere rate limit (429)")

        monkeypatch.setattr("src.controllers.RetrievalController.RetrievalController.search", boom)

        with TestClient(app, raise_server_exceptions=False) as c:
            c.post("/api/v1/data/ingest", json={"doc_keys": ["nice_ng136"]})
            response = c.post(
                "/api/v1/nlp/search",
                json={"query": "hypertension", "mode": "semantic"},
                headers={"Origin": "http://localhost:5173"},
            )

        assert response.status_code == 500
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
        assert "detail" in response.json()
