"""FastAPI application entry point."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.v1.ingest import router as ingest_router
from services.api.v1.search import router as search_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

app = FastAPI(
    title="Geo-RAG AI API",
    description=(
        "**Phase 1 — Ingestion**: Upload ảnh vệ tinh → S3 → Celery → VLM + Embed → ES + Qdrant.\n\n"
        "**Phase 2 — Search**: Semantic search qua vector ANN (Qdrant) + keyword/geo (ES)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(search_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
