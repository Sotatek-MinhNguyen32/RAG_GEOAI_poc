"""Embedding Processor — gọi Jina v4 Embedding API (vLLM-compatible)."""
from typing import List
import httpx
from shared.config import settings

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
        "model": "jinaai/jina-embeddings-v4-vllm-retrieval",
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
            raise RuntimeError("No vector returned from Jina API.")
        
        # Sắp xếp lại để khớp thứ tự của texts
        items_sorted = sorted(items, key=lambda x: x["index"])
        vectors = [item["embedding"] for item in items_sorted]
        
        return vectors
