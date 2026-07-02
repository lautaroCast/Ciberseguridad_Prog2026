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

ENV PYTHONPATH=/app

EXPOSE 8200

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8200"]
