import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.core.guardrails.claim_extraction import ClaimExtractionResult
from src.core.guardrails.gate_classifier import ClassifierVerdict
from src.core.schemas import ClaimSupport, EvidenceItem, GroundedAnswer
from src.helpers.config import get_settings
from src.main import app

FAKE_EMBEDDINGS = DeterministicFakeEmbedding(size=32)


class ReversingFakeReranker(BaseDocumentCompressor):
    def compress_documents(self, documents, query, callbacks=None):
        reversed_docs = list(reversed(documents))
        for i, doc in enumerate(reversed_docs):
            doc.metadata["relevance_score"] = 1.0 - (i / max(len(reversed_docs), 1))
        return reversed_docs


class FakeStructuredRunnable:
    def __init__(self, result):
        self._result = result

    def invoke(self, _messages):
        return self._result


class FakeLlm:
    def __init__(self, results_by_schema: dict):
        self.results_by_schema = results_by_schema

    def with_structured_output(self, schema):
        return FakeStructuredRunnable(self.results_by_schema[schema])


@pytest.fixture(autouse=True)
def fake_backends_and_small_golden_set(monkeypatch, tmp_path):
    monkeypatch.setattr("src.controllers.IngestionController.get_embeddings", lambda settings: FAKE_EMBEDDINGS)
    monkeypatch.setattr("src.main.get_embeddings", lambda settings: FAKE_EMBEDDINGS)
    monkeypatch.setattr(
        "src.controllers.RetrievalController.get_reranker",
        lambda settings, top_n=None: ReversingFakeReranker(),
    )

    golden_path = tmp_path / "golden.jsonl"
    golden_path.write_text(
        json.dumps(
            {
                "qid": "D1", "question": "What is the first-line treatment?", "category": "direct",
                "relevant_chunk_ids": [], "anchors": [], "expected_behavior": "answer", "notes": "",
            }
        )
        + "\n"
        + json.dumps(
            {
                "qid": "O1", "question": "What is the recommended first-line treatment for type 2 diabetes?",
                "category": "out_of_scope", "relevant_chunk_ids": [], "anchors": [],
                "expected_behavior": "refuse", "notes": "",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("src.routes.evaluation.GOLDEN_PATH", golden_path)

    runs_dir = tmp_path / "runs"
    monkeypatch.setattr("src.routes.evaluation.RUNS_DIR", runs_dir)

    settings = get_settings()
    original_collection = settings.VECTOR_COLLECTION_NAME
    test_collection_name = f"wiqaya_e2e_route_test_{uuid.uuid4().hex[:8]}"
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


class TestEvaluateE2ERoute:
    def test_runs_the_golden_set_and_saves_a_report(self):
        with TestClient(app) as c:
            c.post("/api/v1/data/ingest", json={"doc_keys": ["nice_ng136"]})

            search = c.post("/api/v1/nlp/search", json={"query": "ACE inhibitor", "mode": "hybrid_rerank", "k": 1}).json()
            chunk = search["results"][0]["chunk"]
            chunk_id = chunk["metadata"]["chunk_id"]
            chunk_text = chunk["text"]

            raw_answer = GroundedAnswer(
                recommendation="Offer an ACE inhibitor as first-line treatment.",
                evidence=[EvidenceItem(quote=chunk_text, chunk_id=chunk_id)],
                insufficient_evidence=False,
                caveats=[],
            )
            c.app.state.llm = FakeLlm(
                {
                    ClassifierVerdict: ClassifierVerdict(verdict="ALLOW", reason="in-scope"),
                    GroundedAnswer: raw_answer,
                    ClaimExtractionResult: ClaimExtractionResult(claims=[ClaimSupport(claim="c", supported=True)]),
                }
            )

            response = c.post("/api/v1/evaluation/e2e")

        assert response.status_code == 200
        body = response.json()
        assert body["golden_set_size"] == 2
        assert "citation_accuracy" in body
        assert "unsupported_claim_rate" in body
        assert "refusal_correctness" in body
        assert body["refusal_correctness"] == 1.0
        assert "category_breakdown" in body
        assert Path(body["report_path"]).exists()
