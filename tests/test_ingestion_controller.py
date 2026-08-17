import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.controllers.IngestionController import IngestionController
from tests.conftest import make_settings

FAKE_EMBEDDINGS = DeterministicFakeEmbedding(size=32)


@pytest.fixture(autouse=True)
def fake_embeddings(monkeypatch):
    monkeypatch.setattr(
        "src.controllers.IngestionController.get_embeddings",
        lambda settings: FAKE_EMBEDDINGS,
    )


@pytest.fixture(autouse=True)
def clean_pgvector_chunk_rows():
    import psycopg

    dsn = "host=localhost port=5500 user=postgres password=postgres dbname=wiqaya"
    with psycopg.connect(dsn) as conn:
        conn.execute("DELETE FROM langchain_pg_embedding WHERE id LIKE 'nice_ng136-%' OR id LIKE 'who_hypertension-%'")
        conn.commit()
    yield
    with psycopg.connect(dsn) as conn:
        conn.execute("DELETE FROM langchain_pg_embedding WHERE id LIKE 'nice_ng136-%' OR id LIKE 'who_hypertension-%'")
        conn.commit()


def ingest_settings(**overrides):
    import uuid

    return make_settings(VECTOR_COLLECTION_NAME=f"wiqaya_ingest_test_{uuid.uuid4().hex[:8]}", **overrides)


class TestIngestionControllerBothBackends:
    @pytest.mark.parametrize("backend", ["qdrant", "pgvector"])
    def test_vector_count_matches_chunk_count(self, backend):
        settings = ingest_settings(VECTOR_DB_BACKEND=backend)
        result = IngestionController(settings).ingest("nice_ng136")
        assert result.chunk_count > 0
        assert result.indexed_vector_count == result.chunk_count

    @pytest.mark.parametrize("backend", ["qdrant", "pgvector"])
    def test_writes_both_stage_artifacts(self, backend):
        settings = ingest_settings(VECTOR_DB_BACKEND=backend)
        result = IngestionController(settings).ingest("nice_ng136")
        assert result.pages_path.exists()
        assert result.chunks_path.exists()

    @pytest.mark.parametrize("backend", ["qdrant", "pgvector"])
    def test_reingest_keeps_same_count_not_duplicated(self, backend):
        settings = ingest_settings(VECTOR_DB_BACKEND=backend)
        controller = IngestionController(settings)
        first = controller.ingest("nice_ng136")
        second = controller.ingest("nice_ng136")
        assert second.indexed_vector_count == first.chunk_count

    @pytest.mark.parametrize("backend", ["qdrant", "pgvector"])
    def test_ingesting_a_second_doc_does_not_wipe_the_first(self, backend):
        settings = ingest_settings(VECTOR_DB_BACKEND=backend)
        controller = IngestionController(settings)

        nice_result = controller.ingest("nice_ng136")
        who_result = controller.ingest("who_hypertension")

        from src.stores.vectordb_factory import get_vector_count, get_vectordb

        vectorstore = get_vectordb(settings, FAKE_EMBEDDINGS)
        assert get_vector_count(vectorstore, settings, doc_key="nice_ng136") == nice_result.chunk_count
        assert get_vector_count(vectorstore, settings, doc_key="who_hypertension") == who_result.chunk_count
        assert get_vector_count(vectorstore, settings) == nice_result.chunk_count + who_result.chunk_count


class TestIngestionControllerSmokeQuery:
    def test_query_returns_known_chunk_with_full_metadata(self):
        from src.core.chunking.chunker import chunk_document
        from src.stores.vectordb_factory import get_vectordb

        settings = ingest_settings(VECTOR_DB_BACKEND="qdrant")
        IngestionController(settings).ingest("nice_ng136")

        known_chunk = next(c for c in chunk_document("nice_ng136") if "1.4.39" in c.metadata.recommendation_ids)

        store = get_vectordb(settings, FAKE_EMBEDDINGS)
        results = store.similarity_search(known_chunk.text, k=1)
        assert results
        match = results[0]
        assert match.metadata["chunk_id"] == known_chunk.metadata.chunk_id
        assert match.metadata["document_name"]
        assert match.metadata["page_number"] == 21
        assert match.metadata["source_url"]
