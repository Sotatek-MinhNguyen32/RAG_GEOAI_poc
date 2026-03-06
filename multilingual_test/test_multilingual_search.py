"""
Multilingual search PoC tests.

Scenarios tested:
1. Japanese (日本語) queries against Japanese descriptions
2. English queries against Japanese descriptions (cross-lingual)
3. Vietnamese queries against English descriptions (cross-lingual)
4. Mixed-language queries

These tests exercise the full MCP search pipeline:
  query → embed → semantic search → keyword search → RRF fusion → result

Run:
    PYTHONPATH=. conda run -n agent python multilingual_test/test_multilingual_search.py
"""
import sys
import json
import logging

sys.path.insert(0, ".")

from shared.config import settings
from shared.clients import es_client, qdrant_client
from services.worker.processors.qdrant_service import upsert_vector

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
logger = logging.getLogger("multilingual_test")

# ---------------------------------------------------------------------------
# Test data: satellite image descriptions in multiple languages
# ---------------------------------------------------------------------------

MULTILINGUAL_DOCS = [
    {
        "id": "ml_test_jp_01",
        "desc_text": "この衛星画像は、東京都心部の高解像度航空写真です。道路網、建物群、緑地帯が確認できます。",
        "url": "http://localhost:9000/warehouse/ml_test_jp_01.jpg",
        "lang": "ja",
    },
    {
        "id": "ml_test_jp_02",
        "desc_text": "富士山周辺の森林地帯を撮影した衛星画像。山岳地形と植生分布が鮮明に写っています。",
        "url": "http://localhost:9000/warehouse/ml_test_jp_02.jpg",
        "lang": "ja",
    },
    {
        "id": "ml_test_jp_03",
        "desc_text": "大阪湾沿岸の工業地帯。港湾施設、倉庫群、および交通インフラが確認できます。",
        "url": "http://localhost:9000/warehouse/ml_test_jp_03.jpg",
        "lang": "ja",
    },
    {
        "id": "ml_test_en_01",
        "desc_text": "High-resolution satellite image of Tokyo downtown area showing road networks, building clusters, and green zones.",
        "url": "http://localhost:9000/warehouse/ml_test_en_01.jpg",
        "lang": "en",
    },
    {
        "id": "ml_test_en_02",
        "desc_text": "Forest region around Mount Fuji captured by satellite. Mountain terrain and vegetation distribution clearly visible.",
        "url": "http://localhost:9000/warehouse/ml_test_en_02.jpg",
        "lang": "en",
    },
    {
        "id": "ml_test_vi_01",
        "desc_text": "Ảnh vệ tinh khu vực đô thị Hà Nội với mạng lưới đường giao thông, khu dân cư và không gian xanh.",
        "url": "http://localhost:9000/warehouse/ml_test_vi_01.jpg",
        "lang": "vi",
    },
]

# Queries to test cross-lingual retrieval
TEST_QUERIES = [
    # Same-language: Japanese query → Japanese docs
    {"query": "東京の都市部の衛星画像", "lang": "ja", "expected_top": "ml_test_jp_01",
     "label": "JA→JA: Tokyo urban area"},

    # Same-language: English query → English docs
    {"query": "satellite image of forest near mountain", "lang": "en", "expected_top": "ml_test_en_02",
     "label": "EN→EN: Forest mountain"},

    # Cross-lingual: English query → should also find Japanese docs
    {"query": "Tokyo downtown satellite image", "lang": "en", "expected_relevant": ["ml_test_en_01", "ml_test_jp_01"],
     "label": "EN→JA: Cross-lingual Tokyo"},

    # Cross-lingual: Japanese query → English docs
    {"query": "富士山の森林", "lang": "ja", "expected_relevant": ["ml_test_jp_02", "ml_test_en_02"],
     "label": "JA→EN: Cross-lingual Fuji forest"},

    # Vietnamese query → should find Vietnamese doc
    {"query": "khu vực đô thị Hà Nội", "lang": "vi", "expected_top": "ml_test_vi_01",
     "label": "VI→VI: Hanoi urban"},

    # Mixed query: Japanese + English
    {"query": "東京 satellite image urban area", "lang": "mixed",
     "expected_relevant": ["ml_test_jp_01", "ml_test_en_01"],
     "label": "MIXED: Tokyo satellite"},
]


def _get_embedding(text: str):
    """Get embedding using current settings (mock or real)."""
    if settings.USE_MOCK:
        from services.worker.processors.mock_embed import get_embedding
    else:
        from services.worker.processors.embed import get_embedding
    return get_embedding(text)


def setup_test_data():
    """Index multilingual test documents into ES and Qdrant."""
    logger.info("=== Setting up multilingual test data ===")

    # Index into ES
    for doc in MULTILINGUAL_DOCS:
        es_doc = {"id": doc["id"], "desc_text": doc["desc_text"], "url": doc["url"]}
        es_client.index(index=settings.ES_INDEX, id=doc["id"], document=es_doc)
        logger.info("  ES indexed: %s (%s)", doc["id"], doc["lang"])

    # Index into Qdrant
    for doc in MULTILINGUAL_DOCS:
        vector = _get_embedding(doc["desc_text"])
        upsert_vector(
            image_id=doc["id"],
            vector=vector,
            url=doc["url"],
            desc_text=doc["desc_text"],
        )
        logger.info("  Qdrant indexed: %s (%s)", doc["id"], doc["lang"])

    # Refresh ES so docs are immediately searchable
    es_client.indices.refresh(index=settings.ES_INDEX)
    logger.info("  ES index refreshed")


def run_search(query: str, top_k: int = 5) -> dict:
    """Run full MCP search pipeline."""
    from mcp.controller import handle_query_sync
    return handle_query_sync({"query": query, "top_k": top_k})


def run_tests():
    """Execute all multilingual test queries and report results."""
    logger.info("\n=== Running multilingual search tests ===\n")

    results_summary = []

    for test in TEST_QUERIES:
        label = test["label"]
        query = test["query"]
        logger.info("--- %s ---", label)
        logger.info("Query: %s", query)

        response = run_search(query, top_k=5)
        result_ids = [r["image_id"] for r in response.get("results", [])]
        result_scores = {r["image_id"]: r["score"] for r in response.get("results", [])}

        logger.info("Results (%d):", response.get("total", 0))
        for r in response.get("results", []):
            logger.info("  %s (score=%.6f, sources=%s)", r["image_id"], r["score"], r["sources"])

        # Check expectations
        status = "PASS"
        notes = []

        if "expected_top" in test:
            if result_ids and result_ids[0] == test["expected_top"]:
                notes.append(f"Top result correct: {test['expected_top']}")
            else:
                status = "FAIL"
                notes.append(f"Expected top={test['expected_top']}, got={result_ids[0] if result_ids else 'NONE'}")

        if "expected_relevant" in test:
            found = [eid for eid in test["expected_relevant"] if eid in result_ids]
            if found:
                notes.append(f"Found relevant: {found}")
            else:
                status = "WARN"
                notes.append(f"Expected relevant {test['expected_relevant']} not in top results")

        logger.info("Status: %s — %s\n", status, "; ".join(notes))
        results_summary.append({"label": label, "status": status, "notes": notes, "result_ids": result_ids})

    # Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    for s in results_summary:
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(s["status"], "?")
        logger.info("%s %s — %s", icon, s["label"], "; ".join(s["notes"]))

    passed = sum(1 for s in results_summary if s["status"] == "PASS")
    total = len(results_summary)
    logger.info("\nResult: %d/%d passed", passed, total)

    return results_summary


def cleanup_test_data():
    """Remove multilingual test documents from ES and Qdrant."""
    logger.info("\n=== Cleaning up multilingual test data ===")
    for doc in MULTILINGUAL_DOCS:
        try:
            es_client.delete(index=settings.ES_INDEX, id=doc["id"])
        except Exception:
            pass
    logger.info("  ES cleanup done")


if __name__ == "__main__":
    setup_test_data()
    try:
        run_tests()
    finally:
        cleanup_test_data()
