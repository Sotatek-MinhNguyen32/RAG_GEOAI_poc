# Geo-RAG AI PoC

Một dự án, hai phase:

| Phase | Folder | Mô tả |
|-------|--------|-------|
| 1 — Ingestion | `services/` | Offline pipeline: S3 → Worker → ES + Qdrant |
| 2 — Search | `mcp/` | MCP Server: Query → Search → Fusion → Response |

Shared code nằm ở `shared/`.

---

## Setup local 

```bash
cp .env.example .env
docker compose up -d          # khởi động ES, Qdrant, Redis, MinIO
```

## RUN FLOW (from data in root -> push data in Minio -> process -> store in ES + Qdrant)

```bash
# Init databases (tạo ES index + Qdrant collection)
conda run -n agent python services/scripts/init_db.py

# Init MinIO bucket policy (cho phép public view ảnh)
conda run -n agent python services/scripts/init_bucket_policy.py

# Upload ảnh mẫu từ ./data lên MinIO
conda run -n agent python services/scripts/upload_data.py

# Khởi động Celery worker (terminal riêng)
conda run -n agent celery -A services.worker.celery_app worker --loglevel=info

# Đẩy job xử lý toàn bộ ảnh (--limit để test nhanh)
conda run -n agent python services/scripts/start_pipeline.py --limit 5
```

> **Qdrant sẽ show ảnh:** 
> - URL format: `http://localhost:9000/warehouse/{image_id}`
> - Được lưu trong Qdrant payload → có thể click xem ảnh trực tiếp

## Real APIs

- **VLM (Qwen):** `http://13.231.114.91:8001/v1/chat/completions` → Image → Description
- **Embedding (Jina):** `http://13.231.181.57:8000/v1/embeddings` → Text → 2048-dim vector

# Đẩy job xử lý toàn bộ ảnh (--limit để test nhanh)
python services/scripts/start_pipeline.py --limit 5
```

---

## Cấu trúc repo & chỗ code vào

```
RAG_GEOAI_poc/
│
├── shared/                          ← code dùng chung — đổi gì báo cả team
│   ├── config.py                    ← Settings (env vars) cho pipeline chính
│   ├── clients.py                   ← ES client, Qdrant client, S3 client
│   ├── schemas.py                   ← Pydantic schemas dùng chung (SearchResult…)
│   └── core/                        ← Config/client cho OpenSearch (AWS prod)
│       ├── config.py                ← Settings với OPENSEARCH_* + QDRANT_COLLECTION_SIZE
│       ├── es_client.py             ← OpenSearchService (dev/prod switching)
│       └── qdrant_client.py         ← QdrantService singleton
│
├── services/                        ← Phase 1: Ingestion pipeline
│   ├── requirements.txt             ← Dependencies cho toàn bộ services/
│   │
│   ├── scripts/                     ← One-time scripts (chạy tay)
│   │   ├── init_db.py               ← [Task #3] Tạo ES index + Qdrant collection
│   │   ├── upload_data.py           ← Upload ảnh từ ./data lên MinIO
│   │   ├── start_pipeline.py        ← [Task #2] Dispatch Celery jobs từ S3
│   │   └── models/
│   │       └── metadata_schema.py   ← [Task #3] Pydantic schema cho geospatial metadata
│   │
│   ├── api/                         ← [Task #2] FastAPI — nhận file, tạo job
│   │   ├── main.py                  ← App FastAPI entry point
│   │   └── v1/
│   │       └── ingest.py            ← POST /upload, GET /jobs/{id}
│   │
│   └── worker/                      ← [Task #1 + #6] Celery worker
│       ├── celery_app.py            ← [Task #1] Celery app + Redis broker config
│       ├── tasks.py                 ← [Task #6] Task process_image (full pipeline)
│       └── processors/              ← [Task #6] Các bước xử lý trong pipeline
│           ├── storage.py           ← Download/upload S3
│           ├── xml_extractor.py     ← Parse .jpg.aux.xml → metadata
│           ├── vlm.py               ← [Task #5] Gọi Qwen VLM → text description
│           ├── embed.py             ← [Task #4] Gọi Jina API → embedding vector
│           ├── index_service.py     ← [Task #7] Lưu doc vào Elasticsearch
│           ├── qdrant_service.py    ← [Task #8] Upsert vector vào Qdrant
│           ├── mock_vlm.py          ← Mock VLM (dùng khi chưa có server)
│           └── mock_embed.py        ← Mock Embed (dùng khi chưa có server)
│
├── mcp/                             ← Phase 2: Search server
│   ├── controller.py                ← Entry point MCP server
│   ├── engines/
│   │   ├── semantic.py              ← [Task #9] Qdrant vector search (Thành Ngô)
│   │   └── keyword.py               ← [Task #10] ES BM25 + geo filter (Tư Nguyễn)
│   └── fusion/
│       ├── rrf.py                   ← [Task #11] Reciprocal Rank Fusion
│       ├── cross_encoder.py         ← [Task #11] Re-ranking
│       ├── quality.py               ← [Task #11] Quality gate
│       ├── formatter.py             ← Format kết quả trả về
│       └── pipeline.py              ← [Task #11] Orchestrate toàn bộ search flow
│
├── docker-compose.yml               ← Infra local: ES 8.15, Qdrant, Redis, MinIO
├── .env.example                     ← Copy → .env rồi điền giá trị
└── documentation/
    ├── tasklist.md                  ← Task list + phân công
    └── phase_1/, phase_2/           ← Flow diagram, sequence diagram
```

---

## Phân công theo từng task

### Minh Nguyễn
| Task | File cần code vào |
|------|-------------------|
| #1 — Celery setup | `services/worker/celery_app.py` ✅ |
| #6 — Worker AI pipeline | `services/worker/tasks.py` + `processors/` ✅ |
| #8 — Lưu vector Qdrant | `services/worker/processors/qdrant_service.py` ✅ |
| #11 — RRF + LLM fusion | `mcp/fusion/rrf.py`, `cross_encoder.py`, `pipeline.py` |

### Tư Nguyễn
| Task | File cần code vào |
|------|-------------------|
| #2 — API S3 + tạo job | `services/api/v1/ingest.py` + `services/scripts/start_pipeline.py` |
| #4 — Jina Embed client | `services/worker/processors/embed.py` ✅ |
| #5 — Qwen VLM client | `services/worker/processors/vlm.py` ✅ |
| #7 — Index vào ES | `services/worker/processors/index_service.py` ✅ |
| #10 — Lexical & Geo search | `mcp/engines/keyword.py` |

### Thành Ngô
| Task | File cần code vào |
|------|-------------------|
| #3 — ES/OpenSearch config | `shared/core/` + `services/scripts/init_db.py` + `services/scripts/models/metadata_schema.py` ✅ |
| #9 — Semantic search | `mcp/engines/semantic.py` |

> **Task #4 & #5 lưu ý:** 
> - **Jina Embedding:** Live tại http://13.231.181.57:8000/v1/embeddings (2048-dim vectors)
> - **Qwen VLM:** Live tại http://13.231.114.91:8001/v1/chat/completions (image → text descriptions)
> - Local: `mock_embed.py` + `mock_vlm.py` có sẵn nếu cần fallback (giữ ở `.gitignore`, không push lên)

---

## Dependency giữa các task

```
Tư (#2): API/start_pipeline ──► Minh (#6): Worker ──► ES + Qdrant
                                    ├── Tư (#4, #5): VLM/Embed clients
                                    ├── Tư (#7): index_service.py
                                    └── Thành (#3): ES mapping/init

Thành (#9): semantic.py ──►
                            Minh (#11): fusion/pipeline.py
Tư (#10):  keyword.py  ──►
```
---

## Current Status (Latest Run)

 ✅ **COMPLETED:**
- All core infrastructure code implemented (Celery, ES, Qdrant, Worker, VLM/Embed APIs)
- Real Qwen VLM and Jina Embedding APIs integrated  
- Boto3 S3 client configured for MinIO compatibility
- Docker environment fully configured with service networking

🔄 **CURRENT WORK:**
- Fixed boto3 endpoint validation issues with MinIO
- Updated docker-compose.yml with proper environment variable overrides for Docker service discovery
- All S3 interaction code (storage.py, upload_data.py, start_pipeline.py) updated for boto3 API
- Database initialization scripts ready

### Quick Test Run

```bash
# Start everything
docker compose -f services/docker-compose.yml up -d

# Initialize databases
PYTHONPATH=. conda run -n agent python services/scripts/init_db.py

# Upload sample data to MinIO  
PYTHONPATH=. conda run -n agent python services/scripts/upload_data.py

# Start Celery worker in a separate terminal
PYTHONPATH=. conda run -n agent celery -A services.worker.celery_app worker -l info

# Queue 1 image for processing
PYTHONPATH=. conda run -n agent python services/scripts/start_pipeline.py --limit 1

# Check results after 30 seconds
curl http://localhost:9200/images_metadata/_count | jq .count
curl http://localhost:6333/collections/desc_embed | jq '.result.points_count'
```

### Known Issues & Solutions

**Issue:** Bucket policy script fails with boto3
- **Solution:** Skip for local dev (direct URLs work fine with public bucket)

**Issue:** Docker worker can't access MinIO  
- **Fix:** Using `geo_minio:9000` (Docker service DNS) in docker-compose environment overrides instead of localhost

**Clean rebuild if issues:**
```bash
docker compose -f services/docker-compose.yml down -v
docker system prune -f
docker compose -f services/docker-compose.yml up -d --build
```