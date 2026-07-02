# Migration runner: builds Alembic + the ORM schema into a minimal image
# whose only job is `alembic upgrade head` against DATABASE_URL, then exit.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY models ./models

ENTRYPOINT ["alembic"]
CMD ["upgrade", "head"]
