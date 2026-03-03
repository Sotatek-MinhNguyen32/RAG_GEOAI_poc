from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="forbid",  # Không cho phép biến lạ
    )

    # ── S3 Configurations ──
    S3_BUCKET: str
    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str

    # ── Elasticsearch Configurations ──
    ES_URL: str
    ES_INDEX: str

    # ── OpenSearch Configurations ──
    OPENSEARCH_HOST: str
    OPENSEARCH_PORT: int
    OPENSEARCH_MODE: str = "dev"

    # ── Qdrant Configurations ──
    QDRANT_URL: str
    QDRANT_COLLECTION: str

    # ── Redis Configurations ──
    REDIS_URL: str

    # ── Embedding ──
    EMBED_URL: str
    EMBED_DIM: int

    # ── VLM ──
    VLM_URL: str


# Load settings và fail fast nếu thiếu biến
try:
    settings = Settings()
except ValidationError as e:
    raise RuntimeError(f"Missing or invalid environment variables:\n{e}")
