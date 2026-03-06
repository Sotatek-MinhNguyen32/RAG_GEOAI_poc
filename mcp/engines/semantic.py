"""Semantic search engine — Qdrant vector search."""
from typing import List, Optional
from shared.config import settings
from shared.clients import qdrant_client
from shared.schemas import SearchResult


def search(query_vector: List[float], top_k: Optional[int] = None, score_threshold: Optional[float] = None) -> List[SearchResult]:
    top_k = top_k or settings.RERANKER_TOP_N

    hits = qdrant_client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
        score_threshold=score_threshold,
        with_payload=True,
    )

    results = []
    for point in hits.points:
        payload = point.payload or {}
        results.append(
            SearchResult(
                id=payload.get("id", str(point.id)),
                score=point.score,
                url=payload.get("url"),
                source="semantic",
            )
        )
    return results


def embed_query(query_text: str) -> List[float]:
    if settings.USE_MOCK:
        from services.worker.processors.mock_embed import get_embedding
    else:
        from services.worker.processors.embed import get_embedding
    return get_embedding(query_text)
