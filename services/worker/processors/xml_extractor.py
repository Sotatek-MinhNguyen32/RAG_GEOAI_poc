"""Extract metadata from PAM dataset XML files."""
import xml.etree.ElementTree as ET
import re
from typing import Optional, Dict, Any

from shared.schemas import (
    GeographicMetadata,
    BoundingBox,
    SpatialMetadata,
    ImageFormatMetadata,
    RasterGridConstraints,
)


class XMLMetadataExtractor:

    @staticmethod
    def extract(xml_content: bytes) -> Dict[str, Any]:
        root = ET.fromstring(xml_content)
        for elem in root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]

        wkt_text = XMLMetadataExtractor._extract_wkt(root)

        return {
            "geographic": XMLMetadataExtractor._extract_geographic(wkt_text),
            "bounding_box": XMLMetadataExtractor._extract_bounding_box(root),
            "spatial": XMLMetadataExtractor._extract_spatial(root),
            "image_format": XMLMetadataExtractor._extract_image_format(root),
            "raster_grid": XMLMetadataExtractor._extract_raster_grid(root),
        }


    @staticmethod
    def _extract_wkt(root: ET.Element) -> str:
        for tag in ("WKT", "SRS"):
            elem = root.find(f".//{tag}")
            if elem is not None and elem.text:
                return elem.text
        return ""

    @staticmethod
    def _get_wkt_value(keyword: str, wkt_text: str) -> Optional[str]:
        if not wkt_text:
            return None
        match = re.search(f'{keyword}\\["([^"]+)"', wkt_text)
        return match.group(1) if match else None

    @staticmethod
    def _get_epsg_code(wkt_text: str) -> Optional[str]:
        if not wkt_text:
            return None
        match = re.search(r'AUTHORITY\["EPSG",\s*"?(\d+)"?\]', wkt_text)
        return f"EPSG: {match.group(1)}" if match else None

    @staticmethod
    def _extract_geographic(wkt_text: str) -> Optional[GeographicMetadata]:
        try:
            geo = GeographicMetadata(
                coordinate_system=XMLMetadataExtractor._get_wkt_value("GEOGCS", wkt_text),
                datum=XMLMetadataExtractor._get_wkt_value("DATUM", wkt_text),
                spheroid=XMLMetadataExtractor._get_wkt_value("SPHEROID", wkt_text),
                prime_meridian=XMLMetadataExtractor._get_wkt_value("PRIMEM", wkt_text),
                unit=XMLMetadataExtractor._get_wkt_value("UNIT", wkt_text),
                epsg_code=XMLMetadataExtractor._get_epsg_code(wkt_text),
            )
            if not any([geo.coordinate_system, geo.datum, geo.epsg_code]):
                return None
            return geo
        except Exception:
            return None

    @staticmethod
    def _extract_bounding_box(root: ET.Element) -> Optional[BoundingBox]:
        try:
            target_gcps = root.find(".//TargetGCPs")
            if target_gcps is None:
                return None

            doubles = [
                float(d.text)
                for d in target_gcps.findall(".//Double")
                if d.text
            ]
            if not doubles:
                return None

            long_vals = [v for v in doubles if v > 100]
            lat_vals = [v for v in doubles if 0 < v < 90]

            if long_vals and lat_vals:
                return BoundingBox(
                    longitude_min=min(long_vals),
                    longitude_max=max(long_vals),
                    latitude_min=min(lat_vals),
                    latitude_max=max(lat_vals),
                )
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_spatial(root: ET.Element) -> Optional[SpatialMetadata]:
        try:
            spatial = SpatialMetadata()

            xy_tol = root.find(".//XYTolerance")
            if xy_tol is not None and xy_tol.text:
                spatial.resolution = xy_tol.text

            source_gcps = root.find(".//SourceGCPs")
            if source_gcps is not None:
                doubles = [
                    float(d.text)
                    for d in source_gcps.findall(".//Double")
                    if d.text
                ]
                if doubles:
                    grid_vals = [v for v in doubles if abs(v) > 180]
                    if grid_vals:
                        spatial.grid_extent = f"{min(grid_vals)} / {max(grid_vals)}"

            x_origin = root.find(".//XOrigin")
            if x_origin is not None and x_origin.text:
                spatial.no_data_value = x_origin.text

            return spatial if spatial.resolution else None
        except Exception:
            return None

    @staticmethod
    def _extract_image_format(root: ET.Element) -> Optional[ImageFormatMetadata]:
        try:
            img_format = ImageFormatMetadata()
            img_meta_values = []

            mdi_mapping = {
                "SOURCE_COLOR_SPACE": "color_space",
                "COMPRESSION": "compression",
                "INTERLEAVE": "interleave",
                "PyramidResamplingType": "pyramid_resampling",
            }

            for mdi in root.findall(".//MDI"):
                key = mdi.get("key")
                value = mdi.text
                if key in mdi_mapping:
                    setattr(img_format, mdi_mapping[key], value)
                    img_meta_values.append(value)

            img_format.format_string = (
                " / ".join(img_meta_values) if img_meta_values else None
            )
            return img_format if img_meta_values else None
        except Exception:
            return None

    @staticmethod
    def _extract_raster_grid(root: ET.Element) -> Optional[RasterGridConstraints]:
        try:
            raster = RasterGridConstraints()

            source_gcps = root.find(".//SourceGCPs")
            if source_gcps is not None:
                doubles = [
                    float(d.text)
                    for d in source_gcps.findall(".//Double")
                    if d.text
                ]
                if doubles:
                    grid_vals = [v for v in doubles if abs(v) > 180]
                    if grid_vals:
                        raster.grid_extent = f"{min(grid_vals)} / {max(grid_vals)}"
                        raster.source_gcp_range = (min(grid_vals), max(grid_vals))

            x_origin = root.find(".//XOrigin")
            if x_origin is not None and x_origin.text:
                raster.no_data_value = x_origin.text

            return raster if raster.grid_extent else None
        except Exception:
            return None
