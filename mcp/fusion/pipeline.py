"""Fusion pipeline: RRF -> Cross-Encoder -> Quality -> Format."""
import logging
from typing import List, Optional

from shared.config import settings
from shared.schemas import SearchResult, FusedResult
from mcp.fusion.rrf import reciprocal_rank_fusion
from mcp.fusion.cross_encoder import rerank
from mcp.fusion.quality import check_quality
from mcp.fusion.formatter import format_response

logger = logging.getLogger(__name__)


async def fuse_and_rank(
    query: str,
    semantic_results: List[SearchResult],
    keyword_results: List[SearchResult],
    *,
    rrf_k: Optional[int] = None,
    top_k: Optional[int] = None,
    reranker_top_n: Optional[int] = None,
    enable_cross_encoder: Optional[bool] = None,
    min_score: Optional[float] = None,
) -> dict:
    rrf_k = rrf_k or settings.RRF_K
    top_k = top_k or settings.SEARCH_TOP_K
    reranker_top_n = reranker_top_n or settings.RERANKER_TOP_N
    enable_ce = enable_cross_encoder if enable_cross_encoder is not None else settings.CROSS_ENCODER_ENABLED

    logger.info(
        "Fusion pipeline: semantic=%d, keyword=%d, rrf_k=%d, top_k=%d",
        len(semantic_results), len(keyword_results), rrf_k, top_k,
    )

    fused = reciprocal_rank_fusion(semantic_results, keyword_results, k=rrf_k)
    logger.info("RRF merged %d unique documents", len(fused))

    if not fused:
        quality = check_quality(fused, min_score=min_score)
        return format_response(query, quality, top_k=top_k)

    if enable_ce:
        fused = rerank(query=query, candidates=fused, top_n=reranker_top_n)

    quality = check_quality(fused, min_score=min_score)
    response = format_response(query, quality, top_k=top_k)

    logger.info(
        "Pipeline complete: %d results returned (quality=%s)",
        response["total"], "PASS" if quality.passed else "FAIL",
    )
    return response


def fuse_and_rank_sync(query: str, semantic_results: List[SearchResult], keyword_results: List[SearchResult], **kwargs) -> dict:
    import asyncio
    return asyncio.run(fuse_and_rank(query, semantic_results, keyword_results, **kwargs))
