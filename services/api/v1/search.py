"""
Search API v1
─────────────
POST /api/v1/search    - Semantic search: query text to Top-K satellite images
"""
import logging
from typing import Optional, List, Dict, Any

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
        description="Text query (English or Vietnamese)",
        examples=["rice paddy field near river"],
    )
    top_k: Optional[int] = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return",
    )
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Filter out results below this score threshold (None = no filtering)",
    )


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResult]


class LexicalSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Input query for lexical search with optional geo filters",
    )
    top_k: Optional[int] = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of lexical results to return",
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional filters. Supports bounding_box",
    )


class LexicalSearchResponse(BaseModel):
    query: str
    keyword_query: str
    filters: Optional[Dict[str, Any]] = None
    total: int
    results: List[SearchResult]


# ──────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────

@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search for satellite images",
    description=(
        "Accept a text query, embed via Jina API, "
        "search ANN vectors in Qdrant, and return Top-K nearest images."
    ),
)
async def semantic_search(body: SearchRequest):
    try:
        from mcp.engines.semantic import embed_query, search as qdrant_search

        # Step 1: text to vector
        query_vector = embed_query(body.query)

        # Step 2: vector to Qdrant ANN to SearchResult list
        results: List[SearchResult] = qdrant_search(
            query_vector=query_vector,
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
        logger.error("[Search API] RuntimeError: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("[Search API] Unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {exc}",
        )


@router.post(
    "/search/lexical",
    response_model=LexicalSearchResponse,
    summary="Branch B: Lexical + Geo Search",
    description=(
        "Run lexical BM25 search directly on Elasticsearch "
        "and return Top-K lexical documents."
    ),
)
async def lexical_search(body: LexicalSearchRequest):
    try:
        from mcp.engines.keyword import search as keyword_search
        keyword_query = body.query

        results: List[SearchResult] = keyword_search(
            query_text=keyword_query,
            top_k=body.top_k,
            filters=body.filters,
        )

        logger.info(
            "[Lexical Search API] query=%r keyword_query=%r top_k=%d -> %d results",
            body.query,
            keyword_query,
            body.top_k,
            len(results),
        )

        return LexicalSearchResponse(
            query=body.query,
            keyword_query=keyword_query,
            filters=body.filters,
            total=len(results),
            results=results,
        )
    except RuntimeError as exc:
        logger.error("[Lexical Search API] RuntimeError: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("[Lexical Search API] Unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {exc}",
        )
