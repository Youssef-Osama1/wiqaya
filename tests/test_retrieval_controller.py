import uuid
from typing import Sequence

import pytest
from langchain_core.documents import Document
from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.controllers.RetrievalController import RetrievalController
from src.stores.bm25_factory import build_bm25_retriever
from src.stores.vectordb_factory import get_vectordb
from tests.conftest import make_settings

FAKE_EMBEDDINGS = DeterministicFakeEmbedding(size=32)

CORPUS = [
    {
        "text": "For adults with hypertension, offer lifestyle advice and consider ACE inhibitor treatment.",
        "metadata": {
            "document_name": "Test Guideline", "page_number": 1, "section_title": "Treatment",
            "chunk_id": "test-p001-aaaa1111", "source_url": "https://example.com", "doc_key": "test_doc",
            "section_path": ["Treatment"], "page_end": None, "token_count": 15,
            "recommendation_ids": ["1.1.1"], "has_cross_reference": False, "printed_page": None,
        },
    },
    {
        "text": "Diabetes management requires regular blood glucose monitoring and dietary control.",
        "metadata": {
            "document_name": "Test Guideline", "page_number": 2, "section_title": "Diabetes",
            "chunk_id": "test-p002-bbbb2222", "source_url": "https://example.com", "doc_key": "test_doc",
            "section_path": ["Diabetes"], "page_end": None, "token_count": 12,
            "recommendation_ids": [], "has_cross_reference": False, "printed_page": None,
        },
    },
    {
        "text": "Blood pressure targets for people with cardiovascular disease should be below 140/90 mmHg.",
        "metadata": {
            "document_name": "Test Guideline", "page_number": 3, "section_title": "Targets",
            "chunk_id": "test-p003-cccc3333", "source_url": "https://example.com", "doc_key": "test_doc",
            "section_path": ["Targets"], "page_end": None, "token_count": 16,
            "recommendation_ids": ["1.2.1"], "has_cross_reference": False, "printed_page": None,
        },
    },
]


def write_chunks_fixture(tmp_path):
    import json

    path = tmp_path / "test_doc_chunks.jsonl"
    with path.open("w") as f:
        for item in CORPUS:
            f.write(json.dumps(item) + "\n")
    return tmp_path


class ReversingFakeReranker(BaseDocumentCompressor):
    def compress_documents(self, documents: Sequence[Document], query: str, callbacks=None) -> Sequence[Document]:
        reversed_docs = list(reversed(documents))
        for i, doc in enumerate(reversed_docs):
            doc.metadata["relevance_score"] = 1.0 - (i / max(len(reversed_docs), 1))
        return reversed_docs


@pytest.fixture
def settings(tmp_path):
    return make_settings(VECTOR_DB_BACKEND="qdrant", VECTOR_COLLECTION_NAME=f"wiqaya_retrieval_test_{uuid.uuid4().hex[:8]}")


@pytest.fixture
def controller(settings, tmp_path):
    write_chunks_fixture(tmp_path)
    bm25 = build_bm25_retriever(["test_doc"], chunks_dir=tmp_path, k=5)

    vectorstore = get_vectordb(settings, FAKE_EMBEDDINGS, embedding_dim=32, fresh=True)
    docs = [Document(page_content=c["text"], metadata=c["metadata"]) for c in CORPUS]
    vectorstore.add_documents(docs)

    yield RetrievalController(settings, vectorstore, bm25, reranker_factory=lambda top_n: ReversingFakeReranker())

    from qdrant_client import QdrantClient

    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    if client.collection_exists(settings.VECTOR_COLLECTION_NAME):
        client.delete_collection(settings.VECTOR_COLLECTION_NAME)


class TestSemanticMode:
    def test_returns_results_with_full_metadata(self, controller):
        result = controller.search("hypertension treatment", mode="semantic", k=2)
        assert result.mode == "semantic"
        assert len(result.results) == 2
        for scored in result.results:
            assert scored.source == "semantic"
            assert scored.chunk.metadata.chunk_id
            assert scored.chunk.metadata.document_name
            assert scored.chunk.metadata.page_number > 0


class TestBm25Mode:
    def test_returns_results_for_matching_query(self, controller):
        result = controller.search("hypertension ACE inhibitor treatment", mode="bm25", k=2)
        assert result.results
        assert result.results[0].chunk.metadata.chunk_id == "test-p001-aaaa1111"
        assert result.results[0].source == "bm25"

    def test_scores_are_real_bm25_scores_not_placeholder(self, controller):
        result = controller.search("hypertension ACE inhibitor treatment", mode="bm25", k=3)
        scores = [r.score for r in result.results]
        assert scores == sorted(scores, reverse=True)
        assert scores[0] > 0


class TestHybridMode:
    def test_returns_results_with_full_metadata(self, controller):
        result = controller.search("hypertension treatment", mode="hybrid", k=2)
        assert result.mode == "hybrid"
        assert len(result.results) <= 2
        for scored in result.results:
            assert scored.source == "hybrid"
            assert scored.chunk.metadata.chunk_id


class TestHybridRerankMode:
    def test_rerank_reorders_candidates(self, controller):
        result = controller.search("hypertension treatment", mode="hybrid_rerank", k=3)
        assert result.mode == "hybrid_rerank"
        assert len(result.results) >= 2
        scores = [r.score for r in result.results]
        assert scores == sorted(scores, reverse=True)

    def test_metadata_present_after_rerank(self, controller):
        result = controller.search("hypertension treatment", mode="hybrid_rerank", k=3)
        for scored in result.results:
            assert scored.chunk.metadata.chunk_id
            assert scored.chunk.metadata.document_name
            assert scored.source == "hybrid_rerank"
