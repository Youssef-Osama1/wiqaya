from langchain_core.embeddings import Embeddings

from src.helpers.config import Settings


def get_embeddings(settings: Settings) -> Embeddings:
    if settings.EMBEDDING_BACKEND == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=settings.EMBEDDING_MODEL_ID, openai_api_key=settings.OPENAI_API_KEY)

    if settings.EMBEDDING_BACKEND == "cohere":
        from langchain_cohere import CohereEmbeddings

        return CohereEmbeddings(model=settings.EMBEDDING_MODEL_ID, cohere_api_key=settings.COHERE_API_KEY)

    raise ValueError(f"Unknown EMBEDDING_BACKEND: {settings.EMBEDDING_BACKEND!r}")
