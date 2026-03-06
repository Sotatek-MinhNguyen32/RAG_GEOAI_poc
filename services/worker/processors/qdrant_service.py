"""Qdrant vector upsert/query for collection desc_embed."""
import hashlib
import uuid as uuid_lib
from typing import List, Optional

from qdrant_client.models import PointStruct, PayloadSchemaType
from shared.clients import qdrant_client
from shared.config import settings


def _image_id_to_uuid(image_id: str) -> str:
    return str(uuid_lib.UUID(bytes=hashlib.md5(image_id.encode()).digest()[:16]))


def upsert_vector(image_id: str, vector: List[float], url: str, desc_text: str = "", collection: Optional[str] = None) -> None:
    collection = collection or settings.QDRANT_COLLECTION
    qdrant_client.upsert(
        collection_name=collection,
        points=[
            PointStruct(
                id=_image_id_to_uuid(image_id),
                vector=vector,
                payload={"id": image_id, "url": url, "desc_text": desc_text},
            )
        ],
    )


def upsert_vectors_batch(items: List[dict], collection: Optional[str] = None, batch_size: int = 64) -> int:
    collection = collection or settings.QDRANT_COLLECTION
    total = 0

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        points = [
            PointStruct(
                id=_image_id_to_uuid(item["image_id"]),
                vector=item["vector"],
                payload={
                    "id": item["image_id"],
                    "url": item["url"],
                },
            )
            for item in batch
        ]

        qdrant_client.upsert(
            collection_name=collection,
            points=points,
        )
        total += len(points)

    return total


def create_payload_index(collection: Optional[str] = None) -> None:
    collection = collection or settings.QDRANT_COLLECTION
    qdrant_client.create_payload_index(
        collection_name=collection,
        field_name="id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print(f"[Qdrant] Payload index created on 'id' field")


def get_collection_info(collection: Optional[str] = None) -> dict:
    collection = collection or settings.QDRANT_COLLECTION
    info = qdrant_client.get_collection(collection_name=collection)
    return {
        "name": collection,
        "points_count": info.points_count,
        "vectors_count": info.vectors_count,
        "status": info.status.value,
        "vector_size": info.config.params.vectors.size,
        "distance": info.config.params.vectors.distance.value,
    }
