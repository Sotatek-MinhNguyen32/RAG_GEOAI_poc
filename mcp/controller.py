"""MCP Controller — Phase 2 search orchestrator."""
import logging
from typing import Dict, Any
from shared.config import settings

logger = logging.getLogger(__name__)


async def handle_query(payload: Dict[str, Any]) -> dict:
    query = payload.get("query", "").strip()
    if not query:
        return {"error": "Missing 'query' field", "total": 0, "results": []}

    filters = payload.get("filters")
    top_k = payload.get("top_k", settings.SEARCH_TOP_K)
    enable_ce = payload.get("enable_cross_encoder", settings.CROSS_ENCODER_ENABLED)

    logger.info("Query: %s | filters=%s | top_k=%d", query, filters, top_k)

    from mcp.engines.semantic import embed_query, search as semantic_search
    query_vector = embed_query(query)
    semantic_results = semantic_search(query_vector)
    logger.info("Semantic: %d results", len(semantic_results))

    from mcp.engines.keyword import search as keyword_search
    keyword_results = keyword_search(query, filters=filters)
    logger.info("Keyword: %d results", len(keyword_results))

    from mcp.fusion.pipeline import fuse_and_rank
    response = await fuse_and_rank(
        query=query,
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        top_k=top_k,
        enable_cross_encoder=enable_ce,
    )
    return response


def handle_query_sync(payload: Dict[str, Any]) -> dict:
    import asyncio
    return asyncio.run(handle_query(payload))
