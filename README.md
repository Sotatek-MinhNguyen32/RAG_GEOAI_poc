# Geo-RAG AI PoC

**Phase 1:** Ingestion pipeline (S3 → ES + Qdrant)  
**Phase 2:** Search server (MCP)

## Quick Start

```bash
pkill -9 -f celery 2>/dev/null; \
docker compose -f services/docker-compose.yml down -v && \
docker compose -f services/docker-compose.yml up -d && \
sleep 15 && \
PYTHONPATH=. conda run -n agent python services/scripts/setup_all.py
```

Verify:
```bash
curl -s http://localhost:9200/images_metadata/_count | python3 -c "import sys,json; print('ES:', json.load(sys.stdin)['count'])"
curl -s http://localhost:6333/collections/desc_embed | python3 -c "import sys,json; print('Qdrant:', json.load(sys.stdin)['result']['points_count'])"
```

## Test Search Branches

### Branch A - Semantic Search (Qdrant)

Endpoint:
- `POST http://localhost:8000/api/v1/search`

Example:
```bash
curl --location 'http://localhost:8000/api/v1/search' \
--header 'Content-Type: application/json' \
--data '{
  "query": "rice paddy near river",
  "top_k": 5
}'
```

What it does:
- Embed query text via Embedding API
- Search vector in Qdrant
- Return Top-K semantic documents

### Branch B - Lexical & Geo Search (Elasticsearch BM25)

Endpoint:
- `POST http://localhost:8000/api/v1/search/lexical`

Example (keyword/BM25 only):
```bash
curl --location 'http://localhost:8000/api/v1/search/lexical' \
--header 'Content-Type: application/json' \
--data '{
  "query": "rice paddy can tho",
  "top_k": 5
}'
```

Example (keyword + bounding box filter):
```bash
curl --location 'http://localhost:8000/api/v1/search/lexical' \
--header 'Content-Type: application/json' \
--data '{
  "query": "rice paddy",
  "top_k": 5,
  "filters": {
  }
}'
```

What it does:
- Run BM25 keyword search on Elasticsearch (`desc_text`)
- Apply geo filter from `filters.bounding_box` when provided
- Return Top-K lexical documents

---

## Folder Structure

- `services/` — Phase 1: Ingestion (scripts, API, worker)
- `mcp/` — Phase 2: Search server
- `shared/` — Common code (config, clients)
- `data/` — Sample images (12 .jpg + metadata .xml)
- `docker-compose.yml` — Local stack: ES, Qdrant, Redis, MinIO