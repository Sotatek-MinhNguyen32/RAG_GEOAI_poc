import boto3
from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from shared.config import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
)

es_client = Elasticsearch(settings.ES_URL)

qdrant_client = QdrantClient(url=settings.QDRANT_URL, check_compatibility=False)
