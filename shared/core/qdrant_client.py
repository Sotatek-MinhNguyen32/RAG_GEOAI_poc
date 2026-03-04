from typing import Optional
from qdrant_client import QdrantClient
from shared.core.config import settings


class QdrantService:
    _instance: Optional["QdrantService"] = None
    _client: Optional[QdrantClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self._client = QdrantClient(url=settings.QDRANT_URL)

    def __getattr__(self, name: str):
        """Proxy attribute access to underlying QdrantClient."""
        return getattr(self._client, name)


qdrant_client = QdrantService()
