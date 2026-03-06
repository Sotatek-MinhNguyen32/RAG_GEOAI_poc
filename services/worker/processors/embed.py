"""Embedding Processor — gọi Jina v4 Embedding API (vLLM-compatible)."""
from typing import List
import httpx
from shared.config import settings

_MODEL = "jinaai/jina-embeddings-v4-vllm-retrieval"


def get_embedding(text: str) -> List[float]:
    """Embed một đoạn text, trả về vector float 2048-dim."""
    if not text or not text.strip():
        raise ValueError("Empty text input.")

    return _embed_batch([text])[0]


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Embed nhiều đoạn text cùng lúc, tiết kiệm round-trip."""
    if not texts:
        return []
    return _embed_batch(texts)


def _embed_batch(texts: List[str]) -> List[List[float]]:
    url = f"{settings.EMBED_URL.rstrip('/')}/v1/embeddings"
    payload = {
        "model": _MODEL,
        "input": texts,
        "encoding_format": "float",
    }

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        result = resp.json()

    items = result.get("data", [])
    if not items:
        raise RuntimeError("Embedding API trả về danh sách rỗng.")

    # Sắp xếp theo index để đảm bảo đúng thứ tự
    items_sorted = sorted(items, key=lambda x: x["index"])
    vectors = [item["embedding"] for item in items_sorted]

    # Validate dimension
    for i, vec in enumerate(vectors):
        if len(vec) != settings.EMBED_DIM:
            raise RuntimeError(
                f"Vector dim mismatch tại index {i}: "
                f"expected={settings.EMBED_DIM}, got={len(vec)}"
            )

    return vectors
