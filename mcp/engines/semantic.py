"""
Branch A — Semantic Search Engine
───────────────────────────────────────────────────────
Luồng:
  clean_query (str)
    → Embedding API (Jina vLLM)  → query_vector [2048-dim]
    → Qdrant vector search        → Top-K scored points
    → List[SearchResult]

Dùng chung SearchResult schema từ shared/schemas.py.
"""
import logging
from typing import List, Optional

import httpx
from qdrant_client.models import Filter, FieldCondition, MatchValue, ScoredPoint

from shared.config import settings
from shared.schemas import SearchResult

logger = logging.getLogger(__name__)

# ── Embedding API config ──────────────────────────────────────────────────────
_EMBED_MODEL = "jinaai/jina-embeddings-v4-vllm-retrieval"
_EMBED_TIMEOUT = 60.0   # seconds


# ─────────────────────────────────────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────────────────────────────────────

def search(
    query: str,
    top_k: int | None = None,
    score_threshold: float | None = None,
    collection: str | None = None,
) -> List[SearchResult]:
    """
    Semantic search: embed query → Qdrant ANN → SearchResult list.

    Args:
        query:           Clean text query đã được tiền xử lý.
        top_k:           Số kết quả tối đa (mặc định từ settings.SEARCH_TOP_K).
        score_threshold: Lọc bỏ kết quả có score < threshold. None = giữ tất cả.
        collection:      Tên Qdrant collection (mặc định từ settings.QDRANT_COLLECTION).

    Returns:
        Danh sách SearchResult, sắp xếp giảm dần theo score.
    """
    if not query or not query.strip():
        logger.warning("[Semantic] Query rỗng, trả về danh sách trống.")
        return []

    top_k     = top_k     or settings.SEARCH_TOP_K
    collection = collection or settings.QDRANT_COLLECTION

    # Step 1: Embed query
    query_vector = _embed_query(query)

    # Step 2: Qdrant ANN search
    points = _qdrant_search(
        query_vector=query_vector,
        collection=collection,
        top_k=top_k,
        score_threshold=score_threshold,
    )

    # Step 3: Map → SearchResult
    return _to_search_results(points)


# ─────────────────────────────────────────────────────────────────────────────
# Internals
# ─────────────────────────────────────────────────────────────────────────────

def _embed_query(query: str) -> List[float]:
    """Gọi Jina Embedding API, trả về vector float."""
    url     = f"{settings.EMBED_URL.rstrip('/')}/v1/embeddings"
    payload = {
        "model":            _EMBED_MODEL,
        "input":            [query],
        "encoding_format":  "float",
    }

    try:
        with httpx.Client(timeout=_EMBED_TIMEOUT) as client:
            resp = client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        items = data.get("data", [])
        if not items:
            raise RuntimeError("Embedding API trả về danh sách rỗng.")

        vector = items[0]["embedding"]

        if len(vector) != settings.EMBED_DIM:
            raise RuntimeError(
                f"Vector dim mismatch: expected={settings.EMBED_DIM}, got={len(vector)}"
            )

        logger.debug("[Semantic] Embedded query dim=%d", len(vector))
        return vector

    except httpx.HTTPStatusError as exc:
        logger.error("[Semantic] Embedding API HTTP error: %s", exc.response.text)
        raise RuntimeError(f"Embedding API thất bại: {exc}") from exc
    except httpx.RequestError as exc:
        logger.error("[Semantic] Embedding API connection error: %s", exc)
        raise RuntimeError(f"Không thể kết nối Embedding API: {exc}") from exc


def _qdrant_search(
    query_vector: List[float],
    collection: str,
    top_k: int,
    score_threshold: Optional[float] = None,
) -> List[ScoredPoint]:
    """Query Qdrant với ANN search, trả về ScoredPoint list."""
    from shared.clients import qdrant_client

    try:
        kwargs: dict = {
            "collection_name": collection,
            "query_vector":    query_vector,
            "limit":           top_k,
            "with_payload":    True,
        }
        if score_threshold is not None:
            kwargs["score_threshold"] = score_threshold

        results = qdrant_client.search(**kwargs)
        logger.info(
            "[Semantic] Qdrant search collection=%s top_k=%d → %d results",
            collection,
            top_k,
            len(results),
        )
        return results

    except Exception as exc:
        logger.error("[Semantic] Qdrant search error: %s", exc)
        raise RuntimeError(f"Qdrant search thất bại: {exc}") from exc


def _to_search_results(points: List[ScoredPoint]) -> List[SearchResult]:
    """Chuyển ScoredPoint của Qdrant → SearchResult schema chung."""
    results: List[SearchResult] = []

    for point in points:
        payload = point.payload or {}
        results.append(
            SearchResult(
                id=payload.get("id", str(point.id)),   # image_id gốc (string)
                score=point.score,
                url=payload.get("url"),
                desc_text=payload.get("desc_text"),     # nếu có lưu trong payload
                metadata=payload.get("metadata"),
                source="semantic",
            )
        )

    return results
