from langchain_core.language_models.chat_models import BaseChatModel

from src.helpers.config import Settings


def get_llm(settings: Settings) -> BaseChatModel:
    temperature = settings.GENERATION_TEMPERATURE if settings.GENERATION_TEMPERATURE is not None else 0.0

    if settings.GENERATION_BACKEND == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=settings.GENERATION_MODEL_ID, temperature=temperature, openai_api_key=settings.OPENAI_API_KEY)

    if settings.GENERATION_BACKEND == "cohere":
        from langchain_cohere import ChatCohere

        return ChatCohere(model=settings.GENERATION_MODEL_ID, temperature=temperature, cohere_api_key=settings.COHERE_API_KEY)

    raise ValueError(f"Unknown GENERATION_BACKEND: {settings.GENERATION_BACKEND!r}")
