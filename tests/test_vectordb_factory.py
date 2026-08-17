import uuid

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.stores.vectordb_factory import delete_by_doc_key, get_vector_count, get_vectordb, to_store_id
from tests.conftest import make_settings

FAKE_EMBEDDINGS = DeterministicFakeEmbedding(size=32)


def unique_collection_name() -> str:
    return f"wiqaya_test_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def qdrant_settings():
    settings = make_settings(VECTOR_DB_BACKEND="qdrant", VECTOR_COLLECTION_NAME=unique_collection_name())
    yield settings
    from qdrant_client import QdrantClient

    client = QdrantClient(url=settings.QDRANT_URL)
    if client.collection_exists(settings.VECTOR_COLLECTION_NAME):
        client.delete_collection(settings.VECTOR_COLLECTION_NAME)


@pytest.fixture
def pgvector_settings():
    settings = make_settings(VECTOR_DB_BACKEND="pgvector", VECTOR_COLLECTION_NAME=unique_collection_name())
    yield settings
    import psycopg

    with psycopg.connect(
        f"host={settings.POSTGRES_HOST} port={settings.POSTGRES_PORT} "
        f"user={settings.POSTGRES_USER} password={settings.POSTGRES_PASSWORD} dbname={settings.POSTGRES_DB}"
    ) as conn:
        conn.execute("DELETE FROM langchain_pg_collection WHERE name = %s", (settings.VECTOR_COLLECTION_NAME,))
        conn.commit()


class TestQdrantBackend:
    def test_fresh_collection_starts_empty(self, qdrant_settings):
        store = get_vectordb(qdrant_settings, FAKE_EMBEDDINGS, embedding_dim=32)
        assert get_vector_count(store, qdrant_settings) == 0

    def test_vector_count_matches_added_documents(self, qdrant_settings):
        store = get_vectordb(qdrant_settings, FAKE_EMBEDDINGS, embedding_dim=32)
        docs = [Document(page_content=f"chunk {i}", metadata={"chunk_id": f"id-{i}"}) for i in range(5)]
        store.add_documents(docs)
        assert get_vector_count(store, qdrant_settings) == 5

    def test_metadata_round_trips_through_search(self, qdrant_settings):
        store = get_vectordb(qdrant_settings, FAKE_EMBEDDINGS, embedding_dim=32)
        store.add_documents([Document(page_content="hypertension guidance", metadata={"chunk_id": "abc123", "page_number": 21})])
        results = store.similarity_search("hypertension guidance", k=1)
        assert results[0].metadata["chunk_id"] == "abc123"
        assert results[0].metadata["page_number"] == 21


class TestPgvectorBackend:
    def test_fresh_collection_starts_empty(self, pgvector_settings):
        store = get_vectordb(pgvector_settings, FAKE_EMBEDDINGS)
        assert get_vector_count(store, pgvector_settings) == 0

    def test_vector_count_matches_added_documents(self, pgvector_settings):
        store = get_vectordb(pgvector_settings, FAKE_EMBEDDINGS)
        docs = [Document(page_content=f"chunk {i}", metadata={"chunk_id": f"id-{i}"}) for i in range(5)]
        store.add_documents(docs)
        assert get_vector_count(store, pgvector_settings) == 5

    def test_metadata_round_trips_through_search(self, pgvector_settings):
        store = get_vectordb(pgvector_settings, FAKE_EMBEDDINGS)
        store.add_documents([Document(page_content="hypertension guidance", metadata={"chunk_id": "abc123", "page_number": 21})])
        results = store.similarity_search("hypertension guidance", k=1)
        assert results[0].metadata["chunk_id"] == "abc123"
        assert results[0].metadata["page_number"] == 21


class TestGetVectorCountByDocKey:
    def test_qdrant_counts_only_matching_doc(self, qdrant_settings):
        store = get_vectordb(qdrant_settings, FAKE_EMBEDDINGS, embedding_dim=32)
        store.add_documents(
            [
                Document(page_content="who chunk 1", metadata={"chunk_id": "who-p001-aaaa", "doc_key": "who_hypertension"}),
                Document(page_content="who chunk 2", metadata={"chunk_id": "who-p002-cccc", "doc_key": "who_hypertension"}),
                Document(page_content="nice chunk", metadata={"chunk_id": "nice-p001-bbbb", "doc_key": "nice_ng136"}),
            ]
        )
        assert get_vector_count(store, qdrant_settings, doc_key="who_hypertension") == 2
        assert get_vector_count(store, qdrant_settings, doc_key="nice_ng136") == 1
        assert get_vector_count(store, qdrant_settings) == 3

    def test_pgvector_counts_only_matching_doc(self, pgvector_settings):
        store = get_vectordb(pgvector_settings, FAKE_EMBEDDINGS)
        store.add_documents(
            [
                Document(page_content="who chunk 1", metadata={"chunk_id": "who-p001-aaaa", "doc_key": "who_hypertension"}),
                Document(page_content="who chunk 2", metadata={"chunk_id": "who-p002-cccc", "doc_key": "who_hypertension"}),
                Document(page_content="nice chunk", metadata={"chunk_id": "nice-p001-bbbb", "doc_key": "nice_ng136"}),
            ]
        )
        assert get_vector_count(store, pgvector_settings, doc_key="who_hypertension") == 2
        assert get_vector_count(store, pgvector_settings, doc_key="nice_ng136") == 1
        assert get_vector_count(store, pgvector_settings) == 3


class TestDeleteByDocKey:
    def test_qdrant_removes_only_target_doc_leaves_others_intact(self, qdrant_settings):
        store = get_vectordb(qdrant_settings, FAKE_EMBEDDINGS, embedding_dim=32)
        store.add_documents(
            [
                Document(page_content="who chunk", metadata={"chunk_id": "who-p001-aaaa", "doc_key": "who_hypertension"}),
                Document(page_content="nice chunk", metadata={"chunk_id": "nice-p001-bbbb", "doc_key": "nice_ng136"}),
            ]
        )
        delete_by_doc_key(store, qdrant_settings, "nice_ng136")
        assert get_vector_count(store, qdrant_settings) == 1
        remaining = store.similarity_search("who chunk", k=1)
        assert remaining[0].metadata["doc_key"] == "who_hypertension"

    def test_pgvector_removes_only_target_doc_leaves_others_intact(self, pgvector_settings):
        store = get_vectordb(pgvector_settings, FAKE_EMBEDDINGS)
        store.add_documents(
            [
                Document(page_content="who chunk", metadata={"chunk_id": "who-p001-aaaa", "doc_key": "who_hypertension"}),
                Document(page_content="nice chunk", metadata={"chunk_id": "nice-p001-bbbb", "doc_key": "nice_ng136"}),
            ]
        )
        delete_by_doc_key(store, pgvector_settings, "nice_ng136")
        assert get_vector_count(store, pgvector_settings) == 1
        remaining = store.similarity_search("who chunk", k=1)
        assert remaining[0].metadata["doc_key"] == "who_hypertension"

    def test_deleting_nonexistent_doc_key_is_a_safe_noop(self, qdrant_settings):
        store = get_vectordb(qdrant_settings, FAKE_EMBEDDINGS, embedding_dim=32)
        store.add_documents([Document(page_content="chunk", metadata={"chunk_id": "id-1", "doc_key": "who_hypertension"})])
        delete_by_doc_key(store, qdrant_settings, "never_ingested_doc")
        assert get_vector_count(store, qdrant_settings) == 1


class TestFreshReingest:
    def test_qdrant_fresh_wipes_prior_content(self, qdrant_settings):
        store = get_vectordb(qdrant_settings, FAKE_EMBEDDINGS, embedding_dim=32)
        store.add_documents([Document(page_content="stale", metadata={"chunk_id": "old"})])
        assert get_vector_count(store, qdrant_settings) == 1

        fresh_store = get_vectordb(qdrant_settings, FAKE_EMBEDDINGS, embedding_dim=32, fresh=True)
        assert get_vector_count(fresh_store, qdrant_settings) == 0

    def test_pgvector_fresh_wipes_prior_content(self, pgvector_settings):
        store = get_vectordb(pgvector_settings, FAKE_EMBEDDINGS)
        store.add_documents([Document(page_content="stale", metadata={"chunk_id": "old"})])
        assert get_vector_count(store, pgvector_settings) == 1

        fresh_store = get_vectordb(pgvector_settings, FAKE_EMBEDDINGS, fresh=True)
        assert get_vector_count(fresh_store, pgvector_settings) == 0


class TestToStoreId:
    def test_pgvector_passes_chunk_id_through_unchanged(self, pgvector_settings):
        assert to_store_id(pgvector_settings, "nice_ng136-p021-9732d2cc") == "nice_ng136-p021-9732d2cc"

    def test_qdrant_maps_chunk_id_to_a_valid_uuid(self, qdrant_settings):
        import uuid

        store_id = to_store_id(qdrant_settings, "nice_ng136-p021-9732d2cc")
        uuid.UUID(store_id)

    def test_qdrant_mapping_is_deterministic(self, qdrant_settings):
        id1 = to_store_id(qdrant_settings, "nice_ng136-p021-9732d2cc")
        id2 = to_store_id(qdrant_settings, "nice_ng136-p021-9732d2cc")
        assert id1 == id2

    def test_qdrant_different_chunk_ids_map_to_different_uuids(self, qdrant_settings):
        id1 = to_store_id(qdrant_settings, "nice_ng136-p021-9732d2cc")
        id2 = to_store_id(qdrant_settings, "nice_ng136-p021-aaaaaaaa")
        assert id1 != id2

    def test_reingesting_the_same_chunk_id_overwrites_not_duplicates(self, qdrant_settings):
        store = get_vectordb(qdrant_settings, FAKE_EMBEDDINGS, embedding_dim=32)
        chunk_id = "nice_ng136-p021-9732d2cc"
        point_id = to_store_id(qdrant_settings, chunk_id)
        store.add_documents([Document(page_content="v1", metadata={"chunk_id": chunk_id})], ids=[point_id])
        store.add_documents([Document(page_content="v2", metadata={"chunk_id": chunk_id})], ids=[point_id])
        assert get_vector_count(store, qdrant_settings) == 1


class TestBothBackendsAgreeOnCount:
    def test_same_chunk_count_indexed_into_both_backends(self, qdrant_settings, pgvector_settings):
        docs = [Document(page_content=f"chunk {i}", metadata={"chunk_id": f"id-{i}"}) for i in range(7)]

        qdrant_store = get_vectordb(qdrant_settings, FAKE_EMBEDDINGS, embedding_dim=32)
        qdrant_store.add_documents(docs)

        pgvector_store = get_vectordb(pgvector_settings, FAKE_EMBEDDINGS)
        pgvector_store.add_documents(docs)

        assert get_vector_count(qdrant_store, qdrant_settings) == get_vector_count(pgvector_store, pgvector_settings) == 7
