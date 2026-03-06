"""Ingest API endpoints."""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from shared.config import settings
from services.worker.celery_app import celery_app

router = APIRouter()


@router.post("/upload")
async def upload_image(
    image: UploadFile = File(...),
    metadata: Optional[UploadFile] = File(None),
):
    """
    Upload image (JPG) with optional metadata (XML) and start async processing.
    """
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files accepted.")
    if metadata and metadata.filename and not metadata.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="Metadata must be XML.")

    image_id = image.filename
    if not image_id:
        raise HTTPException(status_code=400, detail="Image filename is required.")

    try:
        from services.worker.processors import storage as storage_proc

        image_content = await image.read()
        ok = storage_proc.upload_file(image_content, image_id)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3.")

        metadata_id = None
        if metadata:
            metadata_content = await metadata.read()
            metadata_id = f"{image_id}.aux.xml"
            # Only call upload_file if metadata_id is a valid string
            ok = storage_proc.upload_file(metadata_content, metadata_id)
            if not ok:
                raise HTTPException(status_code=500, detail="Failed to upload metadata to S3.")

        from services.worker.tasks import process_image
        task = process_image.delay(image_id=image_id, metadata_id=metadata_id)

        return {
            "status": "processing",
            "image_id": image_id,
            "task_id": task.id,
            "metadata_id": metadata_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{task_id}")
async def get_task_result(task_id: str):
    task_result = celery_app.AsyncResult(task_id)

    if task_result.state == "PENDING":
        return {"status": "PENDING", "task_id": task_id, "result": None}
    elif task_result.state == "SUCCESS":
        return {"status": "SUCCESS", "task_id": task_id, "result": task_result.result}
    elif task_result.state == "FAILURE":
        return {"status": "FAILURE", "task_id": task_id, "result": str(task_result.info)}
    else:
        return {"status": task_result.state, "task_id": task_id, "result": None}


@router.get("/list")
async def list_images():
    from shared.clients import s3_client

    bucket = settings.S3_BUCKET
    try:
        response = s3_client.list_objects_v2(Bucket=bucket)
        objects = response.get("Contents", [])

        images = []
        for obj in objects:
            if obj["Key"].endswith(".jpg"):
                images.append({
                    "image_id": obj["Key"],
                    "size": obj["Size"],
                })

        return {"bucket": bucket, "total": len(images), "images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 error: {e}")
