from shared.core.es_client import es_client
from shared.core.config import settings


def ensure_index_elasticsearch():
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
