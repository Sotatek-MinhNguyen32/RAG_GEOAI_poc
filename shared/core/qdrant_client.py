from qdrant_client import QdrantClient
from shared.core.config import settings


class QdrantService:
    _instance: "QdrantService" | None = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self._client = QdrantClient(url=settings.QDRANT_URL)


qdrant_client = QdrantService()
