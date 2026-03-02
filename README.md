# Geo-RAG AI PoC

Một dự án, hai phase:

| Phase | Folder | Mô tả |
|-------|--------|-------|
| 1 — Ingestion | `services/` | Offline pipeline: S3 → Worker → ES + Qdrant |
| 2 — Search | `mcp/` | MCP Server: Query → Search → Fusion → Response |

Shared code nằm ở `shared/`.

## Setup local

```bash
cp .env.example .env
docker compose up -d        # ES, Qdrant, Redis, MinIO
```

## Xem phân role

→ [ROLES.md](ROLES.md)
