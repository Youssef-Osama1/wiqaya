from typing import Optional

from langchain_cohere import CohereRerank

from src.helpers.config import Settings


def get_reranker(settings: Settings, top_n: Optional[int] = None) -> CohereRerank:
    if settings.RERANKER_BACKEND == "cohere":
        kwargs = {"model": settings.RERANKER_MODEL_ID, "cohere_api_key": settings.COHERE_API_KEY}
        if top_n is not None:
            kwargs["top_n"] = top_n
        return CohereRerank(**kwargs)

    raise ValueError(f"Unknown RERANKER_BACKEND: {settings.RERANKER_BACKEND!r}")
