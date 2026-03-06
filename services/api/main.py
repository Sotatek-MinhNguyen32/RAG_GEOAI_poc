from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.api.v1.ingest import router as ingest_router

app = FastAPI(title="Geo-RAG Ingestion API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router, prefix="/v1/ingest", tags=["Ingest"])


@app.get("/health")
def health():
    from shared.config import settings
    return {"status": "ok", "mock_mode": settings.USE_MOCK}
