# Reports Service — Jinja2 renders HTML/Markdown/JSON directly; PDF is the
# same HTML template rendered again and converted by WeasyPrint, which
# needs Pango/Cairo/GDK-Pixbuf on the system (not pip-installable — they're
# native libraries WeasyPrint binds to via cffi), plus real fonts so PDF
# text doesn't fall back to tofu boxes.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libpangoft2-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libcairo2 \
        libffi-dev \
        shared-mime-info \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY pytest.ini conftest.py ./
COPY tests ./tests

ENV PYTHONPATH=/app

# Least privilege (Módulo 9): plain Python/uvicorn, no binaries that need
# root or special capabilities. /data/reports is a named volume
# (docker-compose.yml) mounted at this same path at runtime — Docker only
# applies a fresh volume's initial ownership from what's baked into the
# image *the first time* that volume is used, so this mkdir+chown matters
# for a brand-new `reports-data` volume. An already-existing volume from
# before this change keeps whatever ownership it had (confirmed the hard
# way: PermissionError writing PDFs until the existing volume's contents
# were rechowned by hand — see the Módulo 9 plan/PROGRESS.md).
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data/reports \
    && chown -R appuser:appuser /app /data/reports
USER appuser

EXPOSE 8200

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200"]
