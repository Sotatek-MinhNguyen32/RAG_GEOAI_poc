"""S3 storage operations (MinIO)."""
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
    bucket = bucket or settings.S3_BUCKET
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_name},
        ExpiresIn=expiration,
    )
