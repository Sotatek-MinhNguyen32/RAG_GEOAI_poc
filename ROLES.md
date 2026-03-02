# Role Assignments

## Cấu trúc repo

```
poc_RAG_GEOAI/
├── shared/                      ← code dùng chung (config, schemas, clients)
├── services/                    ← Phase 1: ingestion pipeline
│   ├── api/                     ← API nhận file, tạo job
│   ├── worker/                  ← Celery worker xử lý ảnh
│   ├── scripts/                 ← init DB, seed data
│   └── docker-compose.yml       ← ES, Qdrant, Redis, MinIO
├── mcp/                         ← Phase 2: MCP search server
│   ├── engines/                 ← semantic search, keyword search
│   ├── fusion/                  ← RRF, quality check
│   └── docker-compose.yml       ← ES, Qdrant
└── documentation/               ← diagrams, tasklist
```

## vai trò

### Minh Nguyễn
| Folder | Việc |
|--------|------|
| `services/worker/` | Celery pipeline: S3 → XML → VLM → ES → Embed → Qdrant |
| `mcp/fusion/` | RRF fusion + quality check |
| `mcp/main.py` | Orchestrator search pipeline |

### Tư Nguyễn
| Folder | Việc |
|--------|------|
| `services/api/` | FastAPI: list S3, tạo job, check status |
| `services/worker/processors/` | VLM client + Embed client |
| `mcp/engines/keyword.py` | ES keyword search |

### Thành Ngô
| Folder | Việc |
|--------|------|
| `services/scripts/` | ES index mapping, Qdrant collection init |
| `mcp/engines/semantic.py` | Qdrant vector search + cross-ref ES |

### Chung (cả 3)
| Folder | Ghi chú |
|--------|---------|
| `shared/` | Đổi gì thì báo team |

## Dependency

```
Tư: API ──push job──► Minh: Worker ──► ES + Qdrant
                         ├── Tư: VLM/Embed client
                         └── Thành: ES mapping

Thành: Semantic ──► Minh: Fusion ◄── Tư: Keyword
```
