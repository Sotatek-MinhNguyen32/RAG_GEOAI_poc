"""E2E test: Semantic + Keyword + MCP Controller."""
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

# ── Test 1: Semantic Search ──
print("=" * 60)
print("TEST 1: Semantic Search (Qdrant)")
print("=" * 60)
from mcp.engines.semantic import embed_query, search as sem_search

qvec = embed_query("satellite image of agricultural area")
print(f"  Query vector dim: {len(qvec)}")
sem_results = sem_search(qvec, top_k=5)
print(f"  Results: {len(sem_results)}")
for r in sem_results[:3]:
    print(f"    [{r.source}] id={r.id}  score={r.score:.4f}")

# ── Test 2: Keyword Search ──
print()
print("=" * 60)
print("TEST 2: Keyword Search (Elasticsearch)")
print("=" * 60)
from mcp.engines.keyword import search as kw_search

kw_results = kw_search("agricultural area remote sensing", top_k=5)
print(f"  Results: {len(kw_results)}")
for r in kw_results[:3]:
    desc = (r.desc_text or "")[:60]
    print(f"    [{r.source}] id={r.id}  score={r.score:.4f}  desc={desc}...")

# ── Test 3: MCP Controller E2E ──
print()
print("=" * 60)
print("TEST 3: MCP Controller (Full Pipeline)")
print("=" * 60)
from mcp.controller import handle_query_sync

response = handle_query_sync(
    {"query": "satellite image of agricultural area", "top_k": 5}
)
print(json.dumps(response, indent=2, ensure_ascii=False, default=str)[:2000])
