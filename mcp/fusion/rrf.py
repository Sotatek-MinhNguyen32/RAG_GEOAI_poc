"""Reciprocal Rank Fusion (RRF) — merge multiple ranked lists.
RRF_score(d) = sum(1 / (k + rank_i(d))) for each list where d appears.
"""
from collections import defaultdict
from typing import List, Optional
from shared.schemas import SearchResult, FusedResult
from shared.config import settings


def reciprocal_rank_fusion(*result_lists: List[SearchResult], k: Optional[int] = None) -> List[FusedResult]:
    k = k or settings.RRF_K

    rrf_scores: dict[str, float] = defaultdict(float)
    doc_data: dict[str, dict] = {}
    doc_sources: dict[str, set] = defaultdict(set)

    for result_list in result_lists:
        for rank, result in enumerate(result_list, start=1):
            rrf_scores[result.id] += 1.0 / (k + rank)
            doc_sources[result.id].add(result.source)

            existing = doc_data.get(result.id)
            if existing is None:
                doc_data[result.id] = {
                    "url": result.url,
                    "desc_text": result.desc_text or "",
                    "metadata": dict(result.metadata) if result.metadata else {},
                }
            else:
                if result.desc_text and len(result.desc_text) > len(existing.get("desc_text") or ""):
                    existing["desc_text"] = result.desc_text
                if result.url and not existing.get("url"):
                    existing["url"] = result.url
                if result.metadata:
                    merged = dict(result.metadata)
                    merged.update(existing.get("metadata") or {})
                    existing["metadata"] = merged

    fused = []
    for doc_id, rrf_score in rrf_scores.items():
        data = doc_data.get(doc_id, {})
        fused.append(
            FusedResult(
                id=doc_id,
                rrf_score=rrf_score,
                final_score=rrf_score,
                url=data.get("url"),
                desc_text=data.get("desc_text"),
                metadata=data.get("metadata"),
                sources=sorted(doc_sources[doc_id]),
            )
        )

    fused.sort(key=lambda r: r.rrf_score, reverse=True)
    return fused
