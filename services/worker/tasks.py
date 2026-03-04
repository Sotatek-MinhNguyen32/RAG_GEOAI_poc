"""Celery task: process one satellite image through the full ingestion pipeline."""
from services.worker.celery_app import celery_app
from shared.config import settings


@celery_app.task(bind=True, name="process_image", acks_late=True, max_retries=3)
def process_image(self, image_id: str, bucket: str | None = None, metadata_id: str | None = None):
    from services.worker.processors import storage as storage_proc
    from services.worker.processors.xml_extractor import XMLMetadataExtractor
    from services.worker.processors.index_service import sync_to_databases

    if settings.USE_MOCK:
        from services.worker.processors import mock_vlm as vlm_proc
        from services.worker.processors import mock_embed as embed_proc
    else:
        from services.worker.processors import vlm as vlm_proc
        from services.worker.processors import embed as embed_proc

    bucket = bucket or settings.S3_BUCKET
    if metadata_id is None:
        metadata_id = f"{image_id}.aux.xml"

    try:
        image_bytes = storage_proc.get_image_bytes(image_id, bucket)

        extracted_metadata = {}
        xml_bytes = storage_proc.get_metadata_bytes(metadata_id, bucket)
        if xml_bytes:
            try:
                extracted_metadata = XMLMetadataExtractor.extract(xml_bytes)
            except Exception:
                pass

        text_desc = vlm_proc.generate_description(image_bytes)
        vector = embed_proc.get_embedding(text_desc)

        sync_to_databases(
            image_id=image_id,
            text_desc=text_desc,
            vector=vector,
            metadata=extracted_metadata,
            bucket=bucket,
        )

        return {
            "status": "success",
            "image_id": image_id,
            "desc_length": len(text_desc),
            "vector_dim": len(vector),
            "metadata_extracted": bool(extracted_metadata),
        }

    except Exception as e:
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
