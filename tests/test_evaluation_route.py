import json
import uuid

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.core.evaluation.golden import load_golden_set
from src.helpers.config import get_settings
from src.main import app
from src.routes import evaluation as evaluation_routes

FAKE_EMBEDDINGS = DeterministicFakeEmbedding(size=32)


class PassthroughFakeReranker(BaseDocumentCompressor):
    def compress_documents(self, documents, query, callbacks=None):
        for i, doc in enumerate(documents):
            doc.metadata["relevance_score"] = 1.0 - (i / max(len(documents), 1))
        return documents


@pytest.fixture(autouse=True)
def fakes_and_isolated_collection(monkeypatch, tmp_path):
    monkeypatch.setattr("src.controllers.IngestionController.get_embeddings", lambda settings: FAKE_EMBEDDINGS)
    monkeypatch.setattr("src.main.get_embeddings", lambda settings: FAKE_EMBEDDINGS)
    monkeypatch.setattr(
        "src.controllers.RetrievalController.get_reranker",
        lambda settings, top_n=None: PassthroughFakeReranker(),
    )

    golden_path = tmp_path / "golden.jsonl"
    golden = load_golden_set
    with golden_path.open("w") as f:
        f.write(
            json.dumps(
                {
                    "qid": "Q1", "question": "hypertension treatment", "category": "direct",
                    "relevant_chunk_ids": [], "anchors": [], "expected_behavior": "answer", "notes": "",
                }
            )
            + "\n"
        )
    monkeypatch.setattr(evaluation_routes, "GOLDEN_PATH", golden_path)
    runs_dir = tmp_path / "runs"
    monkeypatch.setattr(evaluation_routes, "RUNS_DIR", runs_dir)

    settings = get_settings()
    original_collection = settings.VECTOR_COLLECTION_NAME
    test_collection_name = f"wiqaya_eval_route_test_{uuid.uuid4().hex[:8]}"
    settings.VECTOR_COLLECTION_NAME = test_collection_name
    yield runs_dir
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


class TestEvaluationRetrievalRoute:
    def test_returns_matrix_and_saves_report(self, client, fakes_and_isolated_collection):
        runs_dir = fakes_and_isolated_collection
        response = client.post("/api/v1/evaluation/retrieval")
        assert response.status_code == 200
        body = response.json()
        assert body["golden_set_size"] == 1
        assert len(body["matrix"]) == 4 * 3
        assert Path_exists(body["report_path"])
        assert list(runs_dir.glob("retrieval_*.json"))


def Path_exists(path_str: str) -> bool:
    from pathlib import Path

    return Path(path_str).exists()
