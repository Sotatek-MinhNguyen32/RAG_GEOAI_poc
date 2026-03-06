"""Cross-Encoder reranker via Jina Reranker API."""
from typing import List, Optional
import httpx

from shared.config import settings
from shared.schemas import FusedResult


def rerank(query: str, candidates: List[FusedResult], top_n: Optional[int] = None) -> List[FusedResult]:
    if not settings.CROSS_ENCODER_ENABLED:
        return candidates
    if not candidates:
        return candidates

    top_n = top_n or settings.RERANKER_TOP_N
    to_rerank = candidates[:top_n]
    remaining = candidates[top_n:]

    documents = [r.desc_text or r.id for r in to_rerank]

    try:
        scores = _call_jina_reranker(query, documents, top_n)
        for result, score in zip(to_rerank, scores):
            result.rerank_score = score
            result.final_score = score
    except Exception:
        return candidates

    to_rerank.sort(key=lambda r: r.final_score, reverse=True)
    return to_rerank + remaining


def _call_jina_reranker(query: str, documents: List[str], top_n: int) -> List[float]:
    url = f"{settings.EMBED_URL}/v1/rerank"
    payload = {
        "model": "jina-reranker-v2-base-multilingual",
        "query": query,
        "documents": documents,
        "top_n": min(top_n, len(documents)),
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    scores_by_index = {r["index"]: r["relevance_score"] for r in results}
    return [scores_by_index.get(i, 0.0) for i in range(len(documents))]
