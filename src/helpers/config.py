from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    ENV: str = "dev"
    CORS_ORIGINS: str = "http://localhost:5173"

    GENERATION_BACKEND: Literal["openai", "cohere"]
    EMBEDDING_BACKEND: Literal["openai", "cohere"]
    RERANKER_BACKEND: Literal["cohere"]

    OPENAI_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None

    GENERATION_MODEL_ID: str
    GENERATION_TEMPERATURE: float = 0.0

    EMBEDDING_MODEL_ID: str

    RERANKER_MODEL_ID: str

    VECTOR_DB_BACKEND: Literal["pgvector", "qdrant"]
    VECTOR_COLLECTION_NAME: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    QDRANT_URL: str

    CHUNK_TARGET_TOKENS: int
    CHUNK_MAX_TOKENS: int
    CHUNK_MIN_TOKENS: int
    CHUNK_OVERLAP_TOKENS: int

    DEFAULT_TOP_K: int
    RERANK_CANDIDATE_K: int
    HYBRID_WEIGHT_SEMANTIC: float

    SIM_HALT_THRESHOLD: float
    SIM_DOWNGRADE_THRESHOLD: float

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
