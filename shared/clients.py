import boto3
from botocore.config import Config
from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from shared.config import settings

# Configure boto3 for MinIO compatibility
# MinIO is S3-compatible but endpoint validation can be strict
s3_config = Config(
    retries={'max_attempts': 3}
)

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    region_name="us-east-1",
    config=s3_config,
)

es_client = Elasticsearch(settings.ES_URL)

qdrant_client = QdrantClient(url=settings.QDRANT_URL, check_compatibility=False)
