FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared/ ./shared/
COPY services/ ./services/
COPY mcp/ ./mcp/

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Default: run API. Override with command in docker-compose for worker.
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
