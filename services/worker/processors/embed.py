"""Embedding Processor — call Jina v4 Embedding API."""
from typing import List
import httpx
from shared.config import settings


def get_embedding(text: str) -> List[float]:
    if not text:
        raise ValueError("Empty text input.")

    url = f"{settings.EMBED_URL}/v1/embeddings"
    payload = {
        "model": "jina-embeddings-v3",
        "input": text,
        "task": "retrieval.index",
        "dimensions": settings.EMBED_DIM,
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        result = resp.json()

        vector = result.get("data", [{}])[0].get("embedding", [])
        if not vector:
            raise RuntimeError("No vector returned from Embedding Server.")
        return vector
