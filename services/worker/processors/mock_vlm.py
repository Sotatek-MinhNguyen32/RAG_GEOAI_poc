"""Mock VLM Processor — trả về mô tả cố định để test local, KHÔNG push lên remote."""


_MOCK_DESCRIPTION = (
    "This satellite image shows a high-resolution aerial view of an urban and semi-urban area. "
    "The scene contains a mix of residential buildings, roads, green spaces, and infrastructure. "
    "Visible features include road networks, building clusters, vegetation patches, and open land. "
    "The image appears to capture a Vietnamese metropolitan region with moderate development density, "
    "suitable for geospatial analysis and land-use classification tasks."
)


def generate_description(image_bytes: bytes) -> str:
    """Trả về mô tả giả lập cho ảnh vệ tinh (không gọi Qwen VLM server)."""
    if not image_bytes:
        raise ValueError("Empty image bytes.")
    return _MOCK_DESCRIPTION
