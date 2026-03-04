"""
Metadata schema models for geospatial image records in Elasticsearch.
Based on PAM (Pixel And Macro) dataset XML structure.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class GeographicMetadata(BaseModel):
    """Geographic coordinate system metadata (từ WKT/SRS)."""

    coordinate_system: Optional[str] = None  # e.g., "GCS_Tokyo"
    datum: Optional[str] = None  # e.g., "Tokyo" / "D_Tokyo"
    spheroid: Optional[str] = None  # e.g., "Bessel_1841"
    prime_meridian: Optional[str] = None  # e.g., "Greenwich"
    unit: Optional[str] = None  # e.g., "Degree"
    epsg_code: Optional[str] = None  # e.g., "EPSG: 4301"
    meaning: str = "Hệ tọa độ địa lý (Geographic Coordinate System)"


class BoundingBox(BaseModel):
    """Geographic bounding box coordinates."""

    longitude_min: Optional[float] = None
    longitude_max: Optional[float] = None
    latitude_min: Optional[float] = None
    latitude_max: Optional[float] = None

    @property
    def bbox_string(self) -> str:
        """Return bbox as formatted string."""
        if all(
            [
                self.longitude_min,
                self.longitude_max,
                self.latitude_min,
                self.latitude_max,
            ]
        ):
            return f"Lon: {self.longitude_min}/{self.longitude_max}, Lat: {self.latitude_min}/{self.latitude_max}"
        return "Unknown"


class SpatialMetadata(BaseModel):
    """Spatial resolution and grid constraints."""

    resolution: Optional[str] = None  # e.g., "8.984e-09" (XYTolerance)
    grid_extent: Optional[str] = None  # e.g., "-4599.5 / 5799.5" (SourceGCPs range)
    no_data_value: Optional[str] = None  # e.g., "-400" (XOrigin)
    pixel_size: Optional[str] = None  # Pixel dimensions if available
    meaning: str = "Độ phân giải không gian (Spatial Resolution)"


class ImageFormatMetadata(BaseModel):
    """Image file format and technical specifications."""

    color_space: Optional[str] = None  # e.g., "YCbCr"
    compression: Optional[str] = None  # e.g., "JPEG"
    interleave: Optional[str] = None  # e.g., "PIXEL"
    pyramid_resampling: Optional[str] = None  # e.g., "NEAREST"
    format_string: Optional[str] = None  # Combined: "YCbCr / JPEG / PIXEL"
    meaning: str = "Thông số kỹ thuật của tệp hình ảnh (Image Format)"


class RasterGridConstraints(BaseModel):
    """Raster grid constraints and no-data handling."""

    grid_extent: Optional[str] = None
    no_data_value: Optional[str] = None
    source_gcp_range: Optional[tuple] = None  # (min, max) from SourceGCPs
    meaning: str = "Giới hạn lưới điểm ảnh (Raster Grid)"


class ImageMetadata(BaseModel):
    """
    Complete metadata document for an image in Elasticsearch.
    Combines:
    - Image basic info (filename, size, upload time)
    - VLM-generated description
    - Extracted XML metadata (geographic, spatial, format, etc.)
    """

    # Basic info
    image_id: str  # Unique identifier (UUID + filename)
    filename: str  # Original filename (e.g., "50303311.jpg")
    file_size_bytes: Optional[int] = None  # Size of JPG file

    # VLM-generated content
    description: Optional[str] = None  # Text description from VLM

    # Extracted metadata from .jpg.aux.xml
    geographic: Optional[GeographicMetadata] = None
    bounding_box: Optional[BoundingBox] = None
    spatial: Optional[SpatialMetadata] = None
    image_format: Optional[ImageFormatMetadata] = None
    raster_grid: Optional[RasterGridConstraints] = None

    # Tracking fields
    uploaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    # Raw XML content (for reference)
    raw_xml_metadata: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic config for JSON serialization."""

        json_schema_extra = {
            "example": {
                "image_id": "550e8400-e29b-41d4-a716-446655440000_50303311.jpg",
                "filename": "50303311.jpg",
                "file_size_bytes": 125000,
                "description": "Satellite image of geospatial location...",
                "geographic": {
                    "coordinate_system": "GCS_Tokyo",
                    "datum": "Tokyo",
                    "spheroid": "Bessel_1841",
                    "epsg_code": "EPSG: 4301",
                },
                "bounding_box": {
                    "longitude_min": 130.390625,
                    "longitude_max": 130.40625,
                    "latitude_min": 33.593749999999993,
                    "latitude_max": 33.604166666666664,
                },
                "spatial": {
                    "resolution": "8.984e-09",
                    "grid_extent": "-4599.5 / 5799.5",
                },
                "image_format": {
                    "color_space": "YCbCr",
                    "compression": "JPEG",
                    "interleave": "PIXEL",
                },
            }
        }

    def to_es_document(self) -> Dict[str, Any]:
        """Convert to Elasticsearch document format."""
        doc = self.model_dump(exclude_none=True)
        # Ensure datetime fields are ISO format strings for ES
        if self.uploaded_at:
            doc["uploaded_at"] = self.uploaded_at.isoformat()
        if self.processed_at:
            doc["processed_at"] = self.processed_at.isoformat()
        return doc
