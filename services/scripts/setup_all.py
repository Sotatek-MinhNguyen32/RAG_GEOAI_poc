"""
One-shot setup: init DBs → upload data → start pipeline.
Run this once after `docker compose up -d` to kick off the full ingestion.

Usage:
    PYTHONPATH=. python services/scripts/setup_all.py
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def wait_for_services(max_wait: int = 60):
    """Poll until Elasticsearch and Qdrant are ready."""
    from shared.clients import es_client, qdrant_client

    print("⏳ Waiting for services to be healthy...")
    deadline = time.time() + max_wait
    while time.time() < deadline:
        try:
            es_client.cluster.health()
            qdrant_client.get_collections()
            print("✓ All services ready")
            return
        except Exception:
            time.sleep(3)
    raise RuntimeError(f"Services not ready after {max_wait}s")


def run_init_db():
    from services.scripts.init_db import main as init_main
    print("\n─── Step 1: Init Elasticsearch + Qdrant ───")
    init_main()


def run_upload_data():
    from services.scripts.upload_data import upload_data, list_bucket
    print("\n─── Step 2: Upload data to MinIO ───")
    upload_data()
    list_bucket()


def run_start_pipeline():
    from services.scripts.start_pipeline import main as pipeline_main
    print("\n─── Step 3: Queue all images to worker ───")
    pipeline_main()


if __name__ == "__main__":
    wait_for_services()
    run_init_db()
    run_upload_data()
    run_start_pipeline()
    print("\n✅ Setup complete. Worker will now process all images.")
    print("   Monitor: docker compose -f services/docker-compose.yml logs -f worker")
