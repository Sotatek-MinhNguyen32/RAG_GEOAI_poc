import sys, json
sys.path.insert(0, ".")
from mcp.engines.semantic import embed_query, search
from shared.config import settings

q = "rừng núi"
vec = embed_query(q)
print(f"Embed 0..5: {vec[:5]}")
res = search(query_vector=vec, top_k=5)
print(f"Found {len(res)} results")
for r in res:
    print(r.id, r.score)
