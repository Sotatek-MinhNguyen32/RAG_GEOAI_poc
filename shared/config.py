from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    S3_ENDPOINT: str = Field(default="http://localhost:9000")
    S3_PUBLIC_URL: str = Field(default="http://localhost:9000")  # Public-facing URL for stored image links (always localhost for local dev)
    S3_ACCESS_KEY: str = Field(default="admin")
    S3_SECRET_KEY: str = Field(default="12345678")
    S3_BUCKET: str = Field(default="warehouse")

    ES_URL: str = Field(default="http://localhost:9200")
    ES_INDEX: str = Field(default="images_metadata")

    QDRANT_URL: str = Field(default="http://localhost:6333")
    QDRANT_COLLECTION: str = Field(default="desc_embed")

    EMBED_URL: str = Field(default="http://localhost:8001")
    EMBED_DIM: int = Field(default=2048)
    VLM_URL: str = Field(default="http://localhost:8002")
    USE_MOCK: bool = Field(default=True)

    RRF_K: int = Field(default=60)
    SEARCH_TOP_K: int = Field(default=10)
    RERANKER_TOP_N: int = Field(default=20)
    QUALITY_MIN_SCORE: float = Field(default=0.0)
    QUALITY_MIN_RESULTS: int = Field(default=1)
    CROSS_ENCODER_ENABLED: bool = Field(default=True)


settings = Settings()
