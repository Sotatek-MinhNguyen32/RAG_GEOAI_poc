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
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router, prefix="/v1/ingest", tags=["Ingest"])
app.include_router(search_router, tags=["Search"])


@app.get("/health")
def health():
    from shared.config import settings
    return {"status": "ok", "mock_mode": settings.USE_MOCK}
