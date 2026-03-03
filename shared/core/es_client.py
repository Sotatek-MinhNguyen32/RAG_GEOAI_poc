import os
from opensearchpy import OpenSearch, RequestsHttpConnection
import boto3
from requests_aws4auth import AWS4Auth


class OpenSearchService:
    _instance: "OpenSearchService" | None = None
    _client: OpenSearch | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        mode = os.getenv("OPENSEARCH_MODE", "dev").lower()
        host = os.environ["OPENSEARCH_HOST"]
        port = int(os.getenv("OPENSEARCH_PORT", 443))

        if mode == "dev":
            self._client = OpenSearch(
                hosts=[
                    {
                        "host": os.getenv("OPENSEARCH_HOST", host),
                        "port": int(os.getenv("OPENSEARCH_PORT", port)),
                    }
                ],
                use_ssl=False,
                verify_certs=False,
            )
            return

        if mode == "prod":
            region = os.environ["AWS_REGION"]
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


es_client = OpenSearchService()
