from typing import Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
import boto3
from requests_aws4auth import AWS4Auth
from shared.core.config import settings


class OpenSearchService:
    _instance: Optional["OpenSearchService"] = None
    _client: Optional[OpenSearch] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        mode = settings.OPENSEARCH_MODE.lower()
        host = settings.OPENSEARCH_HOST
        port = settings.OPENSEARCH_PORT

        if mode == "dev":
            self._client = OpenSearch(
                hosts=[{"host": host, "port": port}],
                use_ssl=False,
                verify_certs=False,
            )
            return

        if mode == "prod":
            region = settings.OPENSEARCH_REGION
            credentials = boto3.Session().get_credentials()
            frozen_credentials = credentials.get_frozen_credentials()

            awsauth = AWS4Auth(
                frozen_credentials.access_key,
                frozen_credentials.secret_key,
                region,
                "es",
                session_token=frozen_credentials.token,
            )

            self._client = OpenSearch(
                hosts=[{"host": host, "port": port}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
            )
            return

        raise ValueError(f"Invalid OPENSEARCH_MODE: {mode}")

    def __getattr__(self, name: str):
        """Proxy attribute access to underlying OpenSearch client."""
        return getattr(self._client, name)


es_client = OpenSearchService()
