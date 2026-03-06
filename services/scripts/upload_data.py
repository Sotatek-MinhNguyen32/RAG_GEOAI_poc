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
        if not s3_client.bucket_exists(bucket):
            print(f"Bucket '{bucket}' exists")
    except Exception as e:
        print(f"Warning: {e}")

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
            s3_client.stat_object(bucket, object_name)
            skipped += 1
            continue
        except Exception:
            pass

        with open(filepath, "rb") as f:
            file_size = filepath.stat().st_size
            s3_client.put_object(bucket, object_name, f, length=file_size)
        print(f"  {object_name} ({filepath.stat().st_size:,} bytes)")
        uploaded += 1

    print(f"Upload complete: {uploaded} new, {skipped} skipped")


def list_bucket():
    bucket = settings.S3_BUCKET
    objects = s3_client.list_objects(bucket, recursive=True)
    obj_list = list(objects)
    print(f"\nBucket '{bucket}' contains {len(obj_list)} objects:")
    for obj in obj_list:
        print(f"  {obj.object_name:40s}  {obj.size:>10,} bytes")
