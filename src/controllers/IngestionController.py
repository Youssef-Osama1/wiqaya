from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.chunking.chunker import chunk_document, write_chunks_to_jsonl
from src.core.ingestion.pipeline import write_pages_jsonl
from src.helpers.config import Settings
from src.stores.embedding_factory import get_embeddings
from src.stores.vectordb_factory import delete_by_doc_key, get_vector_count, get_vectordb, to_store_id


@dataclass
class IngestionResult:
    doc_key: str
    pages_path: Path
    chunks_path: Path
    chunk_count: int
    indexed_vector_count: int


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _add_batch_with_retry(vectorstore: VectorStore, documents: list[Document], ids: list) -> None:
    vectorstore.add_documents(documents, ids=ids)


class IngestionController:
    def __init__(self, settings: Settings):
        self.settings = settings

    def ingest(
        self,
        doc_key: str,
        target_tokens: Optional[int] = None,
        hard_max_tokens: Optional[int] = None,
        min_tokens: Optional[int] = None,
        overlap_tokens: Optional[int] = None,
        batch_size: int = 64,
        fresh: bool = True,
    ) -> IngestionResult:
        settings = self.settings

        pages_path = write_pages_jsonl(doc_key)

        chunks = chunk_document(
            doc_key,
            target_tokens=target_tokens if target_tokens is not None else settings.CHUNK_TARGET_TOKENS,
            hard_max_tokens=hard_max_tokens if hard_max_tokens is not None else settings.CHUNK_MAX_TOKENS,
            min_tokens=min_tokens if min_tokens is not None else settings.CHUNK_MIN_TOKENS,
            overlap_tokens=overlap_tokens if overlap_tokens is not None else settings.CHUNK_OVERLAP_TOKENS,
        )
        chunks_path = write_chunks_to_jsonl(chunks, doc_key)

        if not chunks:
            return IngestionResult(doc_key, pages_path, chunks_path, chunk_count=0, indexed_vector_count=0)

        embeddings = get_embeddings(settings)
        embedding_dim = len(embeddings.embed_query("dimension probe"))
        vectorstore = get_vectordb(settings, embeddings, embedding_dim=embedding_dim, fresh=False)
        if fresh:
            delete_by_doc_key(vectorstore, settings, doc_key)

        documents = [Document(page_content=chunk.text, metadata=chunk.metadata.model_dump()) for chunk in chunks]
        ids = [to_store_id(settings, chunk.metadata.chunk_id) for chunk in chunks]

        for i in range(0, len(documents), batch_size):
            _add_batch_with_retry(vectorstore, documents[i : i + batch_size], ids[i : i + batch_size])

        indexed_count = get_vector_count(vectorstore, settings, doc_key=doc_key)
        if indexed_count != len(chunks):
            raise RuntimeError(
                f"Post-index assertion failed for {doc_key}: indexed {indexed_count} vectors "
                f"but produced {len(chunks)} chunks"
            )

        return IngestionResult(doc_key, pages_path, chunks_path, len(chunks), indexed_count)
