from src.helpers.config import Settings


def make_settings(**overrides) -> Settings:
    base = dict(
        APP_NAME="wiqaya", APP_VERSION="0.1.0",
        GENERATION_BACKEND="openai", EMBEDDING_BACKEND="openai", RERANKER_BACKEND="cohere",
        GENERATION_MODEL_ID="gpt-4o-mini", EMBEDDING_MODEL_ID="text-embedding-3-small",
        RERANKER_MODEL_ID="rerank-v3.5", VECTOR_DB_BACKEND="qdrant", VECTOR_COLLECTION_NAME="wiqaya_chunks",
        POSTGRES_USER="postgres", POSTGRES_PASSWORD="postgres", POSTGRES_HOST="localhost",
        POSTGRES_PORT=5500, POSTGRES_DB="wiqaya", QDRANT_URL="http://localhost:6333",
        CHUNK_TARGET_TOKENS=600, CHUNK_MAX_TOKENS=800, CHUNK_MIN_TOKENS=120, CHUNK_OVERLAP_TOKENS=80,
        DEFAULT_TOP_K=5, RERANK_CANDIDATE_K=20, HYBRID_WEIGHT_SEMANTIC=0.5,
        SIM_HALT_THRESHOLD=0.3, SIM_DOWNGRADE_THRESHOLD=0.5,
        OPENAI_API_KEY="sk-test", COHERE_API_KEY="test-key",
    )
    base.update(overrides)
    return Settings(**base)
