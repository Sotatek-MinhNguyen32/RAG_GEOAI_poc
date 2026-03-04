from typing import Optional, Tuple
from pydantic import BaseModel


class GeographicMetadata(BaseModel):
    coordinate_system: Optional[str] = None
    datum: Optional[str] = None
    spheroid: Optional[str] = None
    prime_meridian: Optional[str] = None
    unit: Optional[str] = None
    epsg_code: Optional[str] = None


class BoundingBox(BaseModel):
    longitude_min: Optional[float] = None
    longitude_max: Optional[float] = None
    latitude_min: Optional[float] = None
    latitude_max: Optional[float] = None


class SpatialMetadata(BaseModel):
    resolution: Optional[str] = None
    grid_extent: Optional[str] = None
    no_data_value: Optional[str] = None


class ImageFormatMetadata(BaseModel):
    color_space: Optional[str] = None
    compression: Optional[str] = None
    interleave: Optional[str] = None
    pyramid_resampling: Optional[str] = None
    format_string: Optional[str] = None


class RasterGridConstraints(BaseModel):
    grid_extent: Optional[str] = None
    no_data_value: Optional[str] = None
    source_gcp_range: Optional[Tuple[float, float]] = None


class SearchResult(BaseModel):
    id: str
    score: float
    url: Optional[str] = None
    desc_text: Optional[str] = None
    metadata: Optional[dict] = None
    source: str = "unknown"


class FusedResult(BaseModel):
    id: str
    rrf_score: float
    rerank_score: Optional[float] = None
    final_score: float
    url: Optional[str] = None
    desc_text: Optional[str] = None
    metadata: Optional[dict] = None
    sources: list[str] = []
