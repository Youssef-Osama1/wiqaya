from typing import Callable, Optional

from langchain_classic.retrievers import EnsembleRetriever
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from src.core.schemas import Chunk, ChunkMetadata, RetrievalResult, ScoredChunk
from src.helpers.config import Settings
from src.stores.reranker_factory import get_reranker


def _doc_to_chunk(doc: Document) -> Chunk:
    return Chunk(text=doc.page_content, metadata=ChunkMetadata(**doc.metadata))


class RetrievalController:
    def __init__(
        self,
        settings: Settings,
        vectorstore: VectorStore,
        bm25_retriever: BM25Retriever,
        reranker_factory: Optional[Callable] = None,
    ):
        self.settings = settings
        self.vectorstore = vectorstore
        self.bm25_retriever = bm25_retriever
        self._reranker_factory = reranker_factory or (lambda top_n: get_reranker(settings, top_n=top_n))

    def search(self, query: str, mode: str, k: int) -> RetrievalResult:
        if mode == "semantic":
            results = self._semantic(query, k)
        elif mode == "bm25":
            results = self._bm25(query, k)
        elif mode == "hybrid":
            results = self._hybrid(query, k)
        elif mode == "hybrid_rerank":
            results = self._hybrid_rerank(query, k)
        else:
            raise ValueError(f"Unknown retrieval mode: {mode!r}")
        return RetrievalResult(query=query, mode=mode, k=k, results=results)

    def _semantic(self, query: str, k: int) -> list[ScoredChunk]:
        pairs = self.vectorstore.similarity_search_with_score(query, k=k)
        return [ScoredChunk(chunk=_doc_to_chunk(doc), score=float(score), source="semantic") for doc, score in pairs]
    
    def _bm25(self, query: str, k: int) -> list[ScoredChunk]:
        retriever = self.bm25_retriever
        preprocessed = retriever.preprocess_func(query)
        scores = retriever.vectorizer.get_scores(preprocessed)
        paired = sorted(zip(retriever.docs, scores), key=lambda pair: pair[1], reverse=True)[:k]
        return [ScoredChunk(chunk=_doc_to_chunk(doc), score=float(score), source="bm25") for doc, score in paired]

    def _build_ensemble(self, k: int) -> EnsembleRetriever:
        semantic_retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        bm25_variant = self.bm25_retriever.model_copy(update={"k": k})
        semantic_weight = self.settings.HYBRID_WEIGHT_SEMANTIC
        return EnsembleRetriever(
            retrievers=[semantic_retriever, bm25_variant],
            weights=[semantic_weight, 1 - semantic_weight],
        )

    def _hybrid(self, query: str, k: int) -> list[ScoredChunk]:
        docs = self._build_ensemble(k).invoke(query)[:k]
        n = len(docs)
        return [
            ScoredChunk(chunk=_doc_to_chunk(doc), score=1.0 - (i / n) if n else 0.0, source="hybrid")
            for i, doc in enumerate(docs)
        ]

    def _hybrid_rerank(self, query: str, k: int) -> list[ScoredChunk]:
        ensemble = self._build_ensemble(self.settings.RERANK_CANDIDATE_K)
        reranker = self._reranker_factory(k)
        compression_retriever = ContextualCompressionRetriever(base_compressor=reranker, base_retriever=ensemble)
        docs = compression_retriever.invoke(query)
        return [
            ScoredChunk(chunk=_doc_to_chunk(doc), score=float(doc.metadata.get("relevance_score", 0.0)), source="hybrid_rerank")
            for doc in docs
        ]
