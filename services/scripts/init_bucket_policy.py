"""Initialize MinIO bucket policy for public read access.

Run this ONCE after creating buckets to allow public viewing of images
in Qdrant and other applications.
"""
import sys
sys.path.insert(0, '/Users/nnminh322/Desktop/sotatek/RAG_GEOAI_poc')

from shared.clients import s3_client
from shared.config import settings
import json

policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{settings.S3_BUCKET}/*"
        }
    ]
}

try:
    s3_client.put_bucket_policy(Bucket=settings.S3_BUCKET, Policy=json.dumps(policy))
    print(f"✅ Bucket policy set for '{settings.S3_BUCKET}' - public read access enabled")
except Exception as e:
    print(f"❌ Error setting policy: {e}")
    sys.exit(1)
