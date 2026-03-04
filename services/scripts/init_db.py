from shared.core.es_client import es_client
from shared.core.qdrant_client import qdrant_client

from shared.core.config import settings
from qdrant_client.models import VectorParams, Distance


def init_elasticsearch():
    client = es_client

    if client.indices.exists(index=settings.ES_INDEX):
        print(f"Index '{settings.ES_INDEX}' already exists")
        return

    client.indices.create(
        index=settings.ES_INDEX,
        body={
            "settings": {"index": {"knn": True}},
            "mappings": {
                "properties": {
                    # ===== BASIC =====
                    "image_id": {"type": "keyword"},
                    "description": {"type": "text", "analyzer": "standard"},
                    "file_size_bytes": {"type": "long"},
                    "url": {"type": "keyword"},
                    # ===== VECTOR =====
                    "description_vector": {
                        "type": "knn_vector",
                        "dimension": 1536,
                        "method": {
                            "name": "hnsw",
                            "engine": "nmslib",
                            "space_type": "cosinesimil",
                        },
                    },
                    # ===== GEO =====
                    "bounding_box": {"type": "geo_shape"},
                    # ===== METADATA =====
                    "metadata": {
                        "properties": {
                            "geographic": {
                                "properties": {
                                    "coordinate_system": {"type": "keyword"},
                                    "datum": {"type": "keyword"},
                                    "spheroid": {"type": "keyword"},
                                    "prime_meridian": {"type": "keyword"},
                                    "unit": {"type": "keyword"},
                                    "epsg_code": {"type": "keyword"},
                                }
                            },
                            "spatial": {
                                "properties": {
                                    "resolution": {"type": "keyword"},
                                    "grid_extent": {"type": "keyword"},
                                    "no_data_value": {"type": "keyword"},
                                    "pixel_size": {"type": "keyword"},
                                }
                            },
                            "image_format": {
                                "properties": {
                                    "color_space": {"type": "keyword"},
                                    "compression": {"type": "keyword"},
                                    "interleave": {"type": "keyword"},
                                    "pyramid_resampling": {"type": "keyword"},
                                }
                            },
                            "raster_grid": {
                                "properties": {
                                    "grid_extent": {"type": "keyword"},
                                    "no_data_value": {"type": "keyword"},
                                }
                            },
                        }
                    },
                    # ===== TIME =====
                    "uploaded_at": {"type": "date"},
                    "processed_at": {"type": "date"},
                }
            },
        },
    )

    print(f"Created production-ready index '{settings.ES_INDEX}'")


def init_qdrant():
    """Create Qdrant collection if not exists and validate vector size"""
    try:
        collection_name = settings.QDRANT_COLLECTION
        vector_size = settings.QDRANT_COLLECTION_SIZE

        collections = qdrant_client.get_collections()
        existing = next(
            (c for c in collections.collections if c.name == collection_name), None
        )

        if existing:
            # Validate vector size
            info = qdrant_client.get_collection(collection_name)
            current_size = info.config.params.vectors.size

            if current_size != vector_size:
                raise ValueError(
                    f"Vector size mismatch: existing={current_size}, expected={vector_size}"
                )

            print(
                f"Qdrant collection '{collection_name}' already exists "
                f"({current_size}-dim)"
            )
            return

        # Create collection
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

        print(
            f"Created Qdrant collection '{collection_name}' "
            f"({vector_size}-dim, COSINE)"
        )

    except Exception as e:
        print(f"Failed to create Qdrant collection: {e}")
        raise


def main():
    print("Initializing Elasticsearch index...")
    init_elasticsearch()
    print("Initializing Qdrant collection...")
    init_qdrant()
    print("Database initialization complete.")
