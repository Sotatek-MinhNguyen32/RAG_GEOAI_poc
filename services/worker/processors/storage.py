"""S3 storage operations (MinIO).

For production (AWS S3):
  - Use presigned URLs via boto3.generate_presigned_url()
  - URLs are time-limited and cryptographically signed
  
For local dev (MinIO):
  - Use direct public URLs (no signature)
  - Format: http://localhost:9000/bucket/key
"""
import io
from typing import Optional
from shared.clients import s3_client
from shared.config import settings


def get_image_bytes(object_name: str, bucket: Optional[str] = None) -> bytes:
    bucket = bucket or settings.S3_BUCKET
    return s3_client.get_object(Bucket=bucket, Key=object_name)["Body"].read()


def get_metadata_bytes(object_name: str, bucket: Optional[str] = None) -> Optional[bytes]:
    bucket = bucket or settings.S3_BUCKET
    try:
        return s3_client.get_object(Bucket=bucket, Key=object_name)["Body"].read()
    except Exception:
        return None


def upload_file(file_bytes: bytes, object_name: str, bucket: Optional[str] = None) -> bool:
    bucket = bucket or settings.S3_BUCKET
    try:
        s3_client.upload_fileobj(io.BytesIO(file_bytes), bucket, object_name)
        return True
    except Exception:
        return False


def generate_presigned_url(object_name: str, bucket: Optional[str] = None, expiration: int = 86400) -> str:
    """Generate public-accessible URL for S3 object.
    
    For local MinIO dev: direct public URL (http://localhost:9000/bucket/key)
    For production (AWS S3): use presigned URLs with signatures
    """
    bucket = bucket or settings.S3_BUCKET
    
    # Check if using local MinIO (localhost) or production AWS
    if 'localhost' in settings.S3_ENDPOINT or '127.0.0.1' in settings.S3_ENDPOINT:
        # Local MinIO: use direct public URL (avoid presigned signature issues)
        return f"{settings.S3_ENDPOINT.rstrip('/')}/{bucket}/{object_name}"
    else:
        # Production (AWS S3): use presigned URL with signature
        return s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": object_name},
            ExpiresIn=expiration,
        )
