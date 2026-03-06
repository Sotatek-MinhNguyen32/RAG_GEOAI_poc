"""Keyword search engine — Elasticsearch BM25 + geo filter."""
from typing import List, Optional, Dict, Any
from shared.config import settings
from shared.clients import es_client
from shared.schemas import SearchResult


def search(query_text: str, top_k: Optional[int] = None, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
    top_k = top_k or settings.RERANKER_TOP_N

    must_clauses = [{"match": {"desc_text": {"query": query_text, "operator": "or"}}}]

    filter_clauses = []
    if filters:
        bbox = filters.get("bounding_box")
        if bbox:
            filter_clauses.append({
                "bool": {
                    "must": [
                        {"range": {"metadata.bounding_box.longitude_min": {"lte": bbox.get("longitude_max", 180)}}},
                        {"range": {"metadata.bounding_box.longitude_max": {"gte": bbox.get("longitude_min", -180)}}},
                        {"range": {"metadata.bounding_box.latitude_min": {"lte": bbox.get("latitude_max", 90)}}},
                        {"range": {"metadata.bounding_box.latitude_max": {"gte": bbox.get("latitude_min", -90)}}},
                    ]
                }
            })

    body = {
        "query": {
            "bool": {
                "must": must_clauses,
                **({
                    "filter": filter_clauses} if filter_clauses else {}),
            }
        },
        "size": top_k,
        "_source": ["id", "desc_text", "url", "metadata"],
    }

    resp = es_client.search(index=settings.ES_INDEX, body=body)

    results = []
    for hit in resp["hits"]["hits"]:
        source = hit["_source"]
        results.append(
            SearchResult(
                id=source.get("id", hit["_id"]),
                score=hit["_score"],
                url=source.get("url"),
                desc_text=source.get("desc_text"),
                metadata=source.get("metadata"),
                source="keyword",
            )
        )
    return results
