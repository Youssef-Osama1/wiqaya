#!/usr/bin/env python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.controllers.RetrievalController import RetrievalController
from src.core.registry import all_doc_specs
from src.helpers.config import get_settings
from src.stores.bm25_factory import build_bm25_retriever
from src.stores.embedding_factory import get_embeddings
from src.stores.vectordb_factory import get_vectordb


def print_candidates(query: str, n: int = 10) -> None:
    settings = get_settings()
    vectorstore = get_vectordb(settings, get_embeddings(settings))
    bm25 = build_bm25_retriever([spec.doc_key for spec in all_doc_specs()], k=n)
    controller = RetrievalController(settings, vectorstore, bm25)

    for mode in ("semantic", "bm25"):
        result = controller.search(query, mode=mode, k=n)
        print(f"\n=== {mode} top-{len(result.results)} for: {query!r} ===")
        for i, scored in enumerate(result.results, start=1):
            meta = scored.chunk.metadata
            snippet = scored.chunk.text[:150].replace("\n", " ")
            recs = f" recs={meta.recommendation_ids}" if meta.recommendation_ids else ""
            print(f"{i:2d}. [{scored.score:.3f}] {meta.chunk_id}  (p.{meta.page_number}, {meta.document_name}){recs}")
            print(f"     {snippet}...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python eval/label_candidates.py "your question here" [n]')
        sys.exit(1)
    query_arg = sys.argv[1]
    n_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    print_candidates(query_arg, n_arg)
