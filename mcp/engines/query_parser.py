"""Query parser (QA/Geo-NER): extract clean query, keywords, and filters."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

import httpx

from shared.config import settings

logger = logging.getLogger(__name__)


def _safe_json_loads(text: str) -> Dict[str, Any]:
    """Parse JSON payload from model output with basic safety fallbacks."""
    text = (text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return {}
    return {}


def parse_payload(query: str, filters: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Parse user query into:
    - clean_query: text for semantic embedding
    - keyword_query: lexical text for Elasticsearch branch
    - filters: normalized geo filters
    Falls back to input data if parser service is unavailable.
    """
    base_filters = filters or {}
    parser_url = settings.QUERY_PARSER_URL.strip() or settings.VLM_URL.strip()
    parser_url = f"{parser_url.rstrip('/')}/v1/chat/completions"

    system_prompt = (
        "You are a query parser for geo-search.\n"
        "Return ONLY valid compact JSON with keys: clean_query, keyword_query, filters.\n"
        "filters may contain bounding_box with longitude_min, longitude_max, latitude_min, latitude_max.\n"
        "Do not add markdown or explanations."
    )
    user_prompt = (
        "Input query:\n"
        f"{query}\n\n"
        "Input filters (JSON):\n"
        f"{json.dumps(base_filters, ensure_ascii=True)}"
    )

    payload = {
        "model": settings.QUERY_PARSER_MODEL,
        "temperature": 0.0,
        "max_tokens": 256,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy",
    }

    fallback = {
        "clean_query": query,
        "keyword_query": query,
        "filters": base_filters,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(parser_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = _safe_json_loads(content if isinstance(content, str) else "")
        if not parsed:
            logger.warning("Query parser returned non-JSON content; using fallback.")
            return fallback

        clean_query = (parsed.get("clean_query") or query).strip() or query
        keyword_query = (parsed.get("keyword_query") or clean_query).strip() or clean_query
        parsed_filters = parsed.get("filters")
        merged_filters = parsed_filters if isinstance(parsed_filters, dict) else base_filters

        return {
            "clean_query": clean_query,
            "keyword_query": keyword_query,
            "filters": merged_filters,
        }
    except Exception as exc:
        logger.warning("Query parser unavailable, fallback to raw query: %s", exc)
        return fallback
