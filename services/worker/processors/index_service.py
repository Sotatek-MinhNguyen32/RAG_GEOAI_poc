"""Sync data to Elasticsearch + Qdrant."""
from typing import Optional, Dict, Any, List

from shared.clients import es_client
from shared.config import settings
from services.worker.processors import storage as storage_proc
from services.worker.processors import qdrant_service


def _serialize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    for key in ("geographic", "bounding_box", "spatial", "image_format", "raster_grid"):
        val = metadata.get(key)
        if val is None:
            continue
        result[key] = val.model_dump(exclude_none=True) if hasattr(val, "model_dump") else val
    return result


def sync_to_databases(
    image_id: str,
    text_desc: str,
    vector: List[float],
    metadata: Optional[Dict[str, Any]] = None,
    bucket: Optional[str] = None,
):
    presigned_url = storage_proc.generate_presigned_url(image_id, bucket)

    es_doc = {"id": image_id, "desc_text": text_desc, "url": presigned_url}
    if metadata:
        serialized = _serialize_metadata(metadata)
        if serialized:
            es_doc["metadata"] = serialized

    es_client.index(index=settings.ES_INDEX, id=image_id, document=es_doc)

    qdrant_service.upsert_vector(image_id=image_id, vector=vector, url=presigned_url, desc_text=text_desc)
