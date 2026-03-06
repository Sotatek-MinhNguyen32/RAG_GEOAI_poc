"""
Ingest API v1
─────────────
POST /api/v1/upload        — Nhận file ảnh (.jpg) + metadata XML tuỳ chọn,
                             upload lên S3, dispatch Celery job.
GET  /api/v1/jobs/{task_id} — Trả về trạng thái + kết quả của job.
"""
import io
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from shared.clients import s3_client
from shared.config import settings
from services.worker.tasks import process_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ingest"])

# ──────────────────────────────────────────────
# Response schemas
# ──────────────────────────────────────────────

class UploadResponse(BaseModel):
    task_id: str
    image_id: str
    bucket: str
    message: str


class JobStatusResponse(BaseModel):
    task_id: str
    status: str                    # PENDING | STARTED | SUCCESS | FAILURE | RETRY
    result: Optional[dict] = None
    error: Optional[str] = None


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg"}
ALLOWED_XML_TYPES   = {"text/xml", "application/xml", "application/octet-stream"}
MAX_IMAGE_SIZE_MB   = 200


def _ensure_bucket(bucket: str) -> None:
    """Tạo bucket nếu chưa tồn tại."""
    existing = [
        b["Name"]
        for b in s3_client.list_buckets().get("Buckets", [])
    ]
    if bucket not in existing:
        s3_client.create_bucket(Bucket=bucket)
        logger.info("Created bucket: %s", bucket)


def _upload_to_s3(file_bytes: bytes, object_name: str, bucket: str, content_type: str) -> None:
    s3_client.upload_fileobj(
        io.BytesIO(file_bytes),
        bucket,
        object_name,
        ExtraArgs={"ContentType": content_type},
    )


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload ảnh vệ tinh và dispatch Celery job",
    description=(
        "Upload một file ảnh `.jpg` lên S3/MinIO. "
        "Nếu có file metadata XML đi kèm, upload luôn. "
        "Sau đó tự động dispatch Celery task `process_image`."
    ),
)
async def upload_image(
    image: UploadFile = File(..., description="Ảnh vệ tinh định dạng .jpg"),
    metadata: Optional[UploadFile] = File(None, description="File .jpg.aux.xml tuỳ chọn"),
    bucket: Optional[str] = Form(None, description="Tên S3 bucket (mặc định từ .env)"),
):
    # ── Validate content-type ──
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File ảnh phải là JPEG, nhận được: {image.content_type}",
        )

    # ── Đọc bytes ──
    image_bytes = await image.read()

    # ── Validate file size ──
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > MAX_IMAGE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File vượt giới hạn {MAX_IMAGE_SIZE_MB} MB (nhận {size_mb:.1f} MB)",
        )

    # ── Validate filename ──
    if not image.filename or not image.filename.lower().endswith(".jpg"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tên file phải có đuôi .jpg",
        )

    bucket = bucket or settings.S3_BUCKET
    image_id = image.filename  # dùng filename làm object key

    # ── Đảm bảo bucket tồn tại ──
    try:
        _ensure_bucket(bucket)
    except Exception as exc:
        logger.exception("Không thể tạo/kiểm tra bucket")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Lỗi kết nối S3: {exc}",
        )

    # ── Upload ảnh lên S3 ──
    try:
        _upload_to_s3(image_bytes, image_id, bucket, "image/jpeg")
        logger.info("Uploaded image: bucket=%s key=%s size=%.2f MB", bucket, image_id, size_mb)
    except Exception as exc:
        logger.exception("Upload ảnh thất bại")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Upload ảnh thất bại: {exc}",
        )

    # ── Upload XML metadata (tuỳ chọn) ──
    metadata_id: Optional[str] = None
    if metadata is not None:
        xml_bytes = await metadata.read()
        xml_key   = metadata.filename or f"{image_id}.aux.xml"
        try:
            _upload_to_s3(xml_bytes, xml_key, bucket, "application/xml")
            metadata_id = xml_key
            logger.info("Uploaded XML: bucket=%s key=%s", bucket, xml_key)
        except Exception as exc:
            # XML lỗi không chặn pipeline — log warning và tiếp tục
            logger.warning("Upload XML thất bại, tiếp tục không có metadata: %s", exc)

    # ── Dispatch Celery task ──
    try:
        task = process_image.delay(
            image_id=image_id,
            bucket=bucket,
            metadata_id=metadata_id,
        )
        logger.info("Dispatched task: task_id=%s image_id=%s", task.id, image_id)
    except Exception as exc:
        logger.exception("Dispatch Celery task thất bại")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không thể dispatch job: {exc}",
        )

    return UploadResponse(
        task_id=task.id,
        image_id=image_id,
        bucket=bucket,
        message="Job đã được dispatch. Dùng GET /api/v1/jobs/{task_id} để theo dõi.",
    )


@router.get(
    "/jobs/{task_id}",
    response_model=JobStatusResponse,
    summary="Lấy trạng thái và kết quả của job",
    description=(
        "Trả về trạng thái Celery task: PENDING, STARTED, SUCCESS, FAILURE, RETRY. "
        "Nếu SUCCESS sẽ có thêm trường `result` chứa thông tin xử lý ảnh."
    ),
)
async def get_job_status(task_id: str):
    try:
        from celery.result import AsyncResult
        from services.worker.celery_app import celery_app

        result = AsyncResult(task_id, app=celery_app)
        state  = result.state  # PENDING | STARTED | SUCCESS | FAILURE | RETRY

        if state == "SUCCESS":
            return JobStatusResponse(
                task_id=task_id,
                status=state,
                result=result.result,
            )

        if state == "FAILURE":
            error = str(result.result) if result.result else "Unknown error"
            return JobStatusResponse(
                task_id=task_id,
                status=state,
                error=error,
            )

        # PENDING / STARTED / RETRY
        return JobStatusResponse(task_id=task_id, status=state)

    except Exception as exc:
        logger.exception("Lỗi khi truy vấn trạng thái task")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể lấy trạng thái task: {exc}",
        )
