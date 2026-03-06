"""
Search API v1
─────────────
POST /api/v1/search    — Semantic search: query text → Top-K ảnh vệ tinh
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from shared.schemas import SearchResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["search"])


# ──────────────────────────────────────────────
# Request / Response schemas
# ──────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Câu truy vấn văn bản (tiếng Anh hoặc tiếng Việt)",
        examples=["rice paddy field near river"],
    )
    top_k: Optional[int] = Field(
        default=10,
        ge=1,
        le=100,
        description="Số kết quả tối đa trả về",
    )
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Lọc kết quả có score thấp hơn ngưỡng này (None = lấy tất cả)",
    )


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResult]


# ──────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────

@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search ảnh vệ tinh",
    description=(
        "Nhận câu truy vấn văn bản, embed qua Jina API, "
        "tìm kiếm vector ANN trong Qdrant và trả về Top-K ảnh gần nhất."
    ),
)
async def semantic_search(body: SearchRequest):
    try:
        from mcp.engines.semantic import search as semantic_search_fn

        results: List[SearchResult] = semantic_search_fn(
            query=body.query,
            top_k=body.top_k,
            score_threshold=body.score_threshold,
        )

        logger.info(
            "[Search API] query=%r top_k=%d → %d results",
            body.query, body.top_k, len(results),
        )

        return SearchResponse(
            query=body.query,
            total=len(results),
            results=results,
        )

    except RuntimeError as exc:
        # Lỗi từ Embed API hoặc Qdrant — trả 503
        logger.error("[Search API] RuntimeError: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("[Search API] Unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không xác định: {exc}",
        )
