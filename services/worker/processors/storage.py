"""S3 storage operations (MinIO).

For production (AWS S3):
  - Use presigned URLs via presigned URLs
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
    
    Uses S3_PUBLIC_URL (always the external/browser-facing URL, e.g. http://localhost:9000)
    This is separate from S3_ENDPOINT which may be an internal Docker hostname.
    
    For production (AWS S3): generate a proper presigned URL.
    """
    bucket = bucket or settings.S3_BUCKET
    public_base = settings.S3_PUBLIC_URL.rstrip('/')
    
    # Check if using local MinIO or production AWS S3
    if 'amazonaws.com' in public_base or (not any(x in public_base for x in ['localhost', '127.0.0.1', 'minio'])):
        # Production (AWS S3): generate a proper presigned URL
        try:
            return s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_name},
                ExpiresIn=expiration
            )
        except Exception:
            pass
    
    # Local MinIO: direct public URL using public-facing hostname
    return f"{public_base}/{bucket}/{object_name}"
