"""Batch job client: list images from S3 and push Celery tasks."""
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.clients import s3_client
from shared.config import settings
from services.worker.celery_app import celery_app


def list_images_from_s3(bucket: str | None = None) -> list[dict]:
    bucket = bucket or settings.S3_BUCKET
    response = s3_client.list_objects_v2(Bucket=bucket)
    objects = response.get("Contents", [])

    jpg_files = {}
    xml_files = set()

    for obj in objects:
        key = obj["Key"]
        if key.endswith(".jpg"):
            jpg_files[key] = obj["Size"]
        elif key.endswith(".jpg.aux.xml"):
            xml_files.add(key)

    images = []
    for image_id, size in sorted(jpg_files.items()):
        metadata_id = f"{image_id}.aux.xml"
        has_xml = metadata_id in xml_files
        images.append({
            "image_id": image_id,
            "metadata_id": metadata_id if has_xml else None,
            "size": size,
        })

    return images


def push_jobs(images: list[dict], bucket: str | None = None) -> list[str]:
    from services.worker.tasks import process_image

    bucket = bucket or settings.S3_BUCKET
    task_ids = []

    for img in images:
        task = process_image.delay(
            image_id=img["image_id"],
            bucket=bucket,
            metadata_id=img["metadata_id"],
        )
        task_ids.append(task.id)
        print(f"  Pushed: {img['image_id']} -> task={task.id}")

    return task_ids


def main():
    parser = argparse.ArgumentParser(description="Batch Job Client")
    parser.add_argument("--dry-run", action="store_true", help="List only, don't push jobs")
    parser.add_argument("--limit", type=int, default=0, help="Max images to process (0=all)")
    parser.add_argument("--bucket", type=str, default=None, help="Override S3 bucket")
    args = parser.parse_args()

    bucket = args.bucket or settings.S3_BUCKET
    print(f"Bucket: {bucket}")
    print(f"Mock mode: {settings.USE_MOCK}")

    images = list_images_from_s3(bucket)
    print(f"Found {len(images)} images")

    if not images:
        print("No images found. Run upload_data.py first.")
        return

    if args.limit > 0:
        images = images[:args.limit]
        print(f"Limited to {args.limit} images")

    for img in images:
        xml_tag = "XML" if img["metadata_id"] else "no XML"
        print(f"  {img['image_id']:30s}  {img['size']:>10,} bytes  [{xml_tag}]")

    if args.dry_run:
        print("(dry-run mode)")
        return

    print(f"Pushing {len(images)} jobs...")
    task_ids = push_jobs(images, bucket)
    print(f"All {len(task_ids)} jobs pushed.")


if __name__ == "__main__":
    main()
