"""Upload ./data folder to MinIO S3 bucket."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.clients import s3_client
from shared.config import settings

DATA_DIR = ROOT / "data"


def should_upload(filename: str) -> bool:
    return filename.endswith(".jpg") or filename.endswith(".jpg.aux.xml")


def upload_data():
    bucket = settings.S3_BUCKET

    try:
        s3_client.head_bucket(Bucket=bucket)
    except Exception:
        s3_client.create_bucket(Bucket=bucket)
        print(f"Created bucket '{bucket}'")

    if not DATA_DIR.exists():
        print(f"Data directory not found: {DATA_DIR}")
        sys.exit(1)

    files = sorted(f for f in DATA_DIR.iterdir() if f.is_file() and should_upload(f.name))
    print(f"Found {len(files)} files to upload from {DATA_DIR}")

    uploaded = 0
    skipped = 0

    for filepath in files:
        object_name = filepath.name
        try:
            s3_client.head_object(Bucket=bucket, Key=object_name)
            skipped += 1
            continue
        except Exception:
            pass

        with open(filepath, "rb") as f:
            s3_client.upload_fileobj(f, bucket, object_name)
        print(f"  {object_name} ({filepath.stat().st_size:,} bytes)")
        uploaded += 1

    print(f"Upload complete: {uploaded} new, {skipped} skipped")


def list_bucket():
    bucket = settings.S3_BUCKET
    response = s3_client.list_objects_v2(Bucket=bucket)
    objects = response.get("Contents", [])
    print(f"\nBucket '{bucket}' contains {len(objects)} objects:")
    for obj in objects:
        print(f"  {obj['Key']:40s}  {obj['Size']:>10,} bytes")


if __name__ == "__main__":
    upload_data()
    list_bucket()
