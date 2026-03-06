# Geo-RAG AI PoC

Một dự án, hai phase:

| Phase | Folder | Mô tả |
|-------|--------|-------|
| 1 — Ingestion | `services/` | Offline pipeline: S3 → Worker → ES + Qdrant |
| 2 — Search | `mcp/` | MCP Server: Query → Search → Fusion → Response |

Shared code nằm ở `shared/`.

---

## Quick Start (fresh run — 1 lệnh duy nhất)

```bash
# Đảm bảo không có local Celery worker nào đang chạy trước
pkill -9 -f celery 2>/dev/null; \
docker compose -f services/docker-compose.yml down -v && \
docker compose -f services/docker-compose.yml up -d && \
sleep 15 && \
PYTHONPATH=. conda run -n agent python services/scripts/setup_all.py
```

Script `setup_all.py` tự động:
1. Chờ tất cả services healthy
2. Tạo ES index + Qdrant collection
3. Upload 24 files từ `./data` → MinIO (bucket public-read)
4. Đẩy 12 jobs → Celery worker (Docker)

### Kiểm tra kết quả

```bash
# Sau ~30 giây
curl -s http://localhost:9200/images_metadata/_count | python3 -c "import sys,json; print('ES docs:', json.load(sys.stdin)['count'])"
curl -s http://localhost:6333/collections/desc_embed | python3 -c "import sys,json; print('Qdrant vectors:', json.load(sys.stdin)['result']['points_count'])"
```

> **Qdrant image URLs:** `http://localhost:9000/warehouse/{image_id}` — click xem ảnh trực tiếp

---

## APIs

| Service | URL | Ghi chú |
|---------|-----|---------|
| VLM (Qwen) | `http://13.231.114.91:8001/v1/chat/completions` | Image → text description |
| Embedding (Jina) | `http://13.231.181.57:8000/v1/embeddings` | Text → 2048-dim vector |
| MinIO UI | `http://localhost:9001` | Xem files đã upload |
| Qdrant UI | `http://localhost:6333/dashboard` | Xem vectors + payloads |
| Redis Insight | `http://localhost:8001` | Monitor task queue |

> **Mock mode** (khi API không khả dụng): set `USE_MOCK=True` trong `.env.docker`

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

## Current Status

✅ **Phase 1 — Ingestion pipeline hoàn chỉnh:**
- Docker worker xử lý 12/12 ảnh thành công (ES + Qdrant đều có 12 docs)
- Qdrant payload URL đúng: `http://localhost:9000/warehouse/{image_id}` (click xem ảnh được)
- Bucket MinIO public-read (không cần presigned URL)
- Mock mode hoạt động khi VLM/Embed API không khả dụng

🔄 **Phase 2 — Search pipeline:** đang triển khai (`mcp/`)

---

## Lưu ý quan trọng

> **KHÔNG chạy local Celery worker** khi dùng Docker stack — sẽ cạnh tranh task với `geo_worker` container trên cùng Redis queue, dẫn đến tasks bị phân chia ngẫu nhiên.

```bash
# Nếu lỡ tay chạy local worker, kill trước khi fresh restart:
pkill -9 -f celery 2>/dev/null
```