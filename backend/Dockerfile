# Build context is the repo root (see docker-compose.yml `backend.build`),
# not this directory — the image needs both backend/app and database/models,
# since the Backend reuses the same ORM models Alembic migrates (Módulo 1)
# instead of redefining the schema.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY database/models ./models
COPY backend/app ./app
COPY backend/pytest.ini backend/conftest.py ./
COPY backend/tests ./tests
# scripts/integration_test.py (Módulo 9) runs from inside this container —
# it hits the Backend's own public API, driving the real pipeline.
COPY scripts ./scripts

ENV PYTHONPATH=/app

# Least privilege (Módulo 9): plain Python/uvicorn, no binaries that need
# root or special capabilities.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
