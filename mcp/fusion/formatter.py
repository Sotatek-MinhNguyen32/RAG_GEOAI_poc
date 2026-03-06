"""Format final fusion results into JSON response."""
from typing import List, Optional
from shared.schemas import FusedResult
from mcp.fusion.quality import QualityCheckResult


def format_response(query: str, quality_result: QualityCheckResult, top_k: Optional[int] = None) -> dict:
    from shared.config import settings
    top_k = top_k or settings.SEARCH_TOP_K

    results = quality_result.results[:top_k]

    return {
        "query": query,
        "total": len(results),
        "results": [_format_single(r) for r in results],
        "quality": {
            "passed": quality_result.passed,
            "warnings": quality_result.warnings,
        },
    }


def _format_single(result: FusedResult) -> dict:
    output = {
        "image_id": result.id,
        "url": result.url,
        "description": result.desc_text,
        "score": round(result.final_score, 6),
        "sources": result.sources,
    }

    if result.metadata:
        output["metadata"] = result.metadata

    output["_scores"] = {"rrf": round(result.rrf_score, 6)}
    if result.rerank_score is not None:
        output["_scores"]["rerank"] = round(result.rerank_score, 6)

    return output
