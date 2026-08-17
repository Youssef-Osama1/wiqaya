import json
from pathlib import Path

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

DEFAULT_CHUNKS_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def build_bm25_retriever(doc_keys: list[str], chunks_dir: Path = DEFAULT_CHUNKS_DIR, k: int = 5) -> BM25Retriever:
    documents: list[Document] = []
    for doc_key in doc_keys:
        chunks_path = chunks_dir / f"{doc_key}_chunks.jsonl"
        with chunks_path.open(encoding="utf-8") as f:
            for line in f:
                chunk = json.loads(line)
                documents.append(Document(page_content=chunk["text"], metadata=chunk["metadata"]))
    return BM25Retriever.from_documents(documents, k=k)
