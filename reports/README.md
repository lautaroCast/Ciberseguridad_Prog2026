# Reports Service — PDF/HTML/Markdown/JSON export (Módulo 7)

Stateless FastAPI microservice: given a self-contained payload (target,
scan, findings — see [`app/schemas/report.py`](app/schemas/report.py)) and
a `format`, it renders a report file to disk and returns its filename. It
has no database, no knowledge of scan IDs beyond what's in the request, and
calls no other service — the Backend is the only caller, gathers all the
data up front, and persists the resulting `Report` row itself (this
service never touches Postgres, consistent with the Scanner Service's
statelessness from Módulo 4).

## Why push, not pull

The Reports Service could instead have pulled data itself (call the
Backend for target/scan/findings, given just a `scan_id`). Push was chosen
instead — the Backend already has `target_service`/`scan_service`/
`finding_service` in one process, gathering the payload there is one
function call, and it keeps this service simpler to test standalone (feed
it a JSON body, no Backend needed) and easier to reason about (no second
service URL to configure, no partial-fetch failure modes).

## Layout

```
app/
  main.py                 FastAPI app, router registration
  config.py                 REPORTS_OUTPUT_DIR (default /data/reports)
  routers/reports.py          POST /reports (generate), GET /reports/{filename} (download)
  schemas/report.py             Request/response models
  services/report_generator.py    Dispatches format -> renderer, writes the file
  renderers/
    context.py                     Shared: sorts findings by severity, counts them
    html_renderer.py                 Jinja2 -> HTML string (autoescape ON — see below)
    markdown_renderer.py               Jinja2 -> Markdown string (autoescape OFF — see below)
    pdf_renderer.py                      Re-renders the HTML template, converts via WeasyPrint
    json_renderer.py                       Structured JSON dump of the same context
    templates/report.html.jinja2             Single HTML template, shared by the HTML and PDF renderers
    templates/report.md.jinja2                 Markdown template
```

## Autoescaping: HTML/PDF on, Markdown off

Finding titles and descriptions come straight from scan tool output
(Nikto, Nuclei, ZAP...) — a finding literally titled
`<script>alert(1)</script>` is a plausible real result from an XSS-focused
template, not a hypothetical. Reflecting that unescaped into an HTML/PDF
report would be a self-inflicted XSS in the report viewer, so
`html_renderer.py` uses `autoescape=True`. `markdown_renderer.py`
deliberately does **not** escape: Markdown is plain text, not markup — a
`&lt;script&gt;` literal in the .md file would just be wrong, not safer,
since nothing renders that file as HTML on its own.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/reports` | Render a report from a full `ReportRequest` body; returns `{format, filename, generated_at}` |
| GET | `/reports/{filename}` | Download a previously generated file |

`filename` in the download route is caller-controlled input reflected
into a filesystem path — the handler resolves it and re-checks it's still
inside `REPORTS_OUTPUT_DIR` before touching disk, so a path-traversal
attempt (`../../etc/passwd`) 404s instead of reading outside the reports
directory.

## The `pydyf` pin

`requirements.txt` pins `pydyf==0.11.0` explicitly, not just
`weasyprint==62.3` — confirmed by hand while building this module:
without the pin, pip resolved `pydyf==0.12.1`, and every PDF render
crashed with `AttributeError: 'super' object has no attribute
'transform'` inside WeasyPrint's own PDF-writing code (`weasyprint==62.3`
calls a `pydyf.Stream` API that pydyf 0.12 removed). HTML/Markdown/JSON
rendering was unaffected — only PDF touches WeasyPrint/pydyf at all — so
this bug only ever showed up as a `502` from the Backend's
`POST /scans/{id}/reports?format=pdf`, never on the other three formats.

## Running it

Part of the root `docker-compose.yml`. To work on it in isolation:

```bash
docker compose up -d reports
curl http://localhost:${REPORTS_PORT:-8200}/health
```

It's normally called by the Backend (`app/services/report_service.py`
there), via `POST /scans/{scan_id}/reports?format=pdf` on the Backend —
see [`backend/README.md`](../backend/README.md).
