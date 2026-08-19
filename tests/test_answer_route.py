import uuid

import pytest
from fastapi.testclient import TestClient
from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.core.guardrails.gate_classifier import ClassifierVerdict
from src.core.guardrails.claim_extraction import ClaimExtractionResult
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
def fake_embeddings_and_isolated_collection(monkeypatch):
    monkeypatch.setattr("src.controllers.IngestionController.get_embeddings", lambda settings: FAKE_EMBEDDINGS)
    monkeypatch.setattr("src.main.get_embeddings", lambda settings: FAKE_EMBEDDINGS)
    monkeypatch.setattr(
        "src.controllers.RetrievalController.get_reranker",
        lambda settings, top_n=None: ReversingFakeReranker(),
    )

    settings = get_settings()
    original_collection = settings.VECTOR_COLLECTION_NAME
    test_collection_name = f"wiqaya_answer_route_test_{uuid.uuid4().hex[:8]}"
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


class TestAnswerRoute:
    def test_out_of_scope_question_is_refused_without_calling_the_generator(self, monkeypatch):
        llm = FakeLlm({})
        with TestClient(app) as c:
            c.app.state.llm = llm
            c.post("/api/v1/data/ingest", json={"doc_keys": ["nice_ng136"]})
            response = c.post("/api/v1/nlp/answer", json={"query": "What is the recommended first-line treatment for type 2 diabetes?"})

        assert response.status_code == 200
        body = response.json()
        assert body["gate"]["verdict"] == "REFUSE"
        assert body["final"]["confidence"] == "Insufficient Evidence"
        assert body["raw_answer"] is None

    def test_in_scope_question_produces_grounded_answer_with_citations(self):
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
            llm = FakeLlm({
                ClassifierVerdict: ClassifierVerdict(verdict="ALLOW", reason="in-scope hypertension question"),
                GroundedAnswer: raw_answer,
                ClaimExtractionResult: ClaimExtractionResult(claims=[ClaimSupport(claim="ACE inhibitor first-line", supported=True)]),
            })
            c.app.state.llm = llm

            response = c.post("/api/v1/nlp/answer", json={"query": "What is the recommended first-line antihypertensive?"})

        assert response.status_code == 200
        body = response.json()
        assert body["gate"]["verdict"] == "ALLOW"
        assert body["final"]["confidence"] == "High"
        assert len(body["final"]["citations"]) == 1
        assert body["final"]["citations"][0]["chunk_id"] == chunk_id
        assert body["final"]["disclaimer"]

    def test_out_of_scope_question_never_touches_the_vector_store(self, monkeypatch):
        settings = get_settings()
        original_collection = settings.VECTOR_COLLECTION_NAME
        settings.VECTOR_COLLECTION_NAME = f"wiqaya_never_ingested_{uuid.uuid4().hex[:8]}"
        try:
            with TestClient(app) as c:
                c.app.state.llm = FakeLlm({})
                response = c.post("/api/v1/nlp/answer", json={"query": "What is the recommended first-line treatment for type 2 diabetes?"})
                assert response.status_code == 200
                assert response.json()["gate"]["verdict"] == "REFUSE"
        finally:
            settings.VECTOR_COLLECTION_NAME = original_collection

    def test_in_scope_question_before_ingest_returns_503(self, monkeypatch):
        settings = get_settings()
        original_collection = settings.VECTOR_COLLECTION_NAME
        settings.VECTOR_COLLECTION_NAME = f"wiqaya_never_ingested_{uuid.uuid4().hex[:8]}"
        try:
            with TestClient(app) as c:
                c.app.state.llm = FakeLlm({ClassifierVerdict: ClassifierVerdict(verdict="ALLOW", reason="in-scope")})
                response = c.post("/api/v1/nlp/answer", json={"query": "Is a blood pressure reading of 135 over 88 too high?"})
                assert response.status_code == 503
        finally:
            settings.VECTOR_COLLECTION_NAME = original_collection
