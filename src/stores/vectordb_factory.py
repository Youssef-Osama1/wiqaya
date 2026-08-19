import uuid
from typing import Optional, Union

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from src.helpers.config import Settings

_QDRANT_ID_NAMESPACE = uuid.UUID("5c1e7f3a-6b0f-4a9a-9b1f-9a7b6d4e3c2f")


def get_vectordb(
    settings: Settings,
    embeddings: Embeddings,
    embedding_dim: Optional[int] = None,
    fresh: bool = False,
) -> VectorStore:
    if settings.VECTOR_DB_BACKEND == "pgvector":
        from langchain_postgres.vectorstores import PGVector

        return PGVector(
            embeddings=embeddings,
            collection_name=settings.VECTOR_COLLECTION_NAME,
            connection=settings.postgres_dsn,
            use_jsonb=True,
            pre_delete_collection=fresh,
        )

    if settings.VECTOR_DB_BACKEND == "qdrant":
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        from langchain_qdrant import QdrantVectorStore

        client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        exists = client.collection_exists(settings.VECTOR_COLLECTION_NAME)
        if exists and fresh:
            client.delete_collection(settings.VECTOR_COLLECTION_NAME)
            exists = False
        if not exists:
            if embedding_dim is None:
                raise ValueError("embedding_dim is required to create a new Qdrant collection")
            client.create_collection(
                settings.VECTOR_COLLECTION_NAME,
                vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
            )
        _ensure_doc_key_index(client, settings.VECTOR_COLLECTION_NAME)
        return QdrantVectorStore(client=client, collection_name=settings.VECTOR_COLLECTION_NAME, embedding=embeddings)

    raise ValueError(f"Unknown VECTOR_DB_BACKEND: {settings.VECTOR_DB_BACKEND!r}")


def _ensure_doc_key_index(client, collection_name: str) -> None:
    from qdrant_client.models import PayloadSchemaType

    if "metadata.doc_key" in (client.get_collection(collection_name).payload_schema or {}):
        return
    client.create_payload_index(
        collection_name=collection_name,
        field_name="metadata.doc_key",
        field_schema=PayloadSchemaType.KEYWORD,
    )


def to_store_id(settings: Settings, chunk_id: str) -> Union[str, int]:
    if settings.VECTOR_DB_BACKEND == "qdrant":
        return str(uuid.uuid5(_QDRANT_ID_NAMESPACE, chunk_id))
    return chunk_id


def delete_by_doc_key(vectorstore: VectorStore, settings: Settings, doc_key: str) -> None:
    if settings.VECTOR_DB_BACKEND == "qdrant":
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        vectorstore.client.delete(
            collection_name=settings.VECTOR_COLLECTION_NAME,
            points_selector=Filter(must=[FieldCondition(key="metadata.doc_key", match=MatchValue(value=doc_key))]),
        )
        return

    if settings.VECTOR_DB_BACKEND == "pgvector":
        with vectorstore._make_sync_session() as session:
            collection = vectorstore.get_collection(session)
            if collection is None:
                return
            session.query(vectorstore.EmbeddingStore).filter(
                vectorstore.EmbeddingStore.collection_id == collection.uuid,
                vectorstore.EmbeddingStore.cmetadata["doc_key"].astext == doc_key,
            ).delete(synchronize_session=False)
            session.commit()
        return

    raise ValueError(f"Unknown VECTOR_DB_BACKEND: {settings.VECTOR_DB_BACKEND!r}")


def get_vector_count(vectorstore: VectorStore, settings: Settings, doc_key: Optional[str] = None) -> int:
    if settings.VECTOR_DB_BACKEND == "qdrant":
        if doc_key is None:
            return vectorstore.client.count(collection_name=settings.VECTOR_COLLECTION_NAME).count
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        count_filter = Filter(must=[FieldCondition(key="metadata.doc_key", match=MatchValue(value=doc_key))])
        return vectorstore.client.count(collection_name=settings.VECTOR_COLLECTION_NAME, count_filter=count_filter).count

    if settings.VECTOR_DB_BACKEND == "pgvector":
        with vectorstore._make_sync_session() as session:
            collection = vectorstore.get_collection(session)
            if collection is None:
                return 0
            query = session.query(vectorstore.EmbeddingStore).filter(
                vectorstore.EmbeddingStore.collection_id == collection.uuid
            )
            if doc_key is not None:
                query = query.filter(vectorstore.EmbeddingStore.cmetadata["doc_key"].astext == doc_key)
            return query.count()

    raise ValueError(f"Unknown VECTOR_DB_BACKEND: {settings.VECTOR_DB_BACKEND!r}")
