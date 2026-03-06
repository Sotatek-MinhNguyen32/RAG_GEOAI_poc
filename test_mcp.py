import sys, json
sys.path.insert(0, ".")
from mcp.controller import handle_query_sync

res = handle_query_sync({"query": "rừng núi", "top_k": 5})
print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
