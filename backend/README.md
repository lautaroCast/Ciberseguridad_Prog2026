# Backend — API core

FastAPI service that owns the schema (reuses [`database/models`](../database/models)
verbatim, see [`Dockerfile`](Dockerfile)) and exposes the platform's REST API.
Target registration (Módulo 3) plus scan lifecycle, raw-result ingestion and
normalization (Módulo 5) live here; reports are added in a later module
against the same layering.

## Layout

```
app/
  main.py              FastAPI app, CORS, router registration
  config.py             Settings from environment variables (pydantic-settings)
  database.py            SQLAlchemy engine/session, get_db() dependency
  routers/                HTTP layer — request/response only, no business logic
  services/                Business rules (e.g. the lab whitelist, ingest orchestration)
  repositories/             Plain DB queries, no rules
  schemas/                   Pydantic request/response models
  normalization/              Tool-specific parsers: RawScanResult -> Service/Technology/Finding rows
```

Each layer only talks to the one below it: routers call services, services
call repositories, repositories call the DB. Business rules that matter
(like "can this host ever be scanned?") live in `services/`, not scattered
across routers — that's the layer every future consumer (the pipeline via
n8n, the frontend, tests) can trust without re-checking.

Domain exceptions raised by the service layer (`TargetNotFoundError`,
`TargetNotAllowedError`, `TargetNameConflictError`) are translated to HTTP
responses by exception handlers registered once in `main.py`, not by
per-route `try/except` blocks — routers just call the service and let
errors propagate. Future resources (scans, findings) reuse the same
mechanism by raising their own exception types.

## The lab whitelist

`app/services/target_service.py::register_target` rejects any `host` not
present in `BACKEND_ALLOWED_LAB_HOSTS` (comma-separated env var, see
`.env.example`) with `422 Unprocessable Entity`. Clients cannot set
`is_lab_target` themselves — it's derived server-side from that check. This
is the enforcement point referenced in [`docs/lab.md`](../docs/lab.md):
network segmentation keeps the rest of the platform off `lab-network`, and
this whitelist keeps arbitrary hosts out of the `targets` table in the
first place.

`BACKEND_ALLOWED_LAB_HOSTS` has no default and fails startup (a Pydantic
`ValidationError`, not a silent empty whitelist) if it's missing or blank —
otherwise the service would boot healthy and then reject every target
registration with no indication the cause is misconfiguration rather than a
real whitelist violation.

Target name uniqueness is checked twice: an optimistic pre-check (fast path,
good error messages) and the database's own unique constraint on
`targets.name` as the actual source of truth, since the pre-check alone
isn't atomic with the insert. A concurrent duplicate `POST` therefore still
gets a clean `409`, not an unhandled `500` from a race on the pre-check.

## Endpoints (Módulo 3)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness + DB connectivity check (used by the Docker healthcheck) |
| GET | `/targets?is_active=` | List targets, optionally filtered |
| POST | `/targets` | Register a target (`name`, `host`, `description`) — `host` must be whitelisted |
| GET | `/targets/{id}` | Fetch one target |
| PATCH | `/targets/{id}` | Update `description` and/or `is_active` (name/host are immutable). Omitted fields are left untouched; sending `"description": null` explicitly clears it — the two are distinguished via Pydantic's `exclude_unset`. |
| DELETE | `/targets/{id}` | Remove a target (cascades to its scan history) |

## Endpoints (Módulo 5)

| Method | Path | Description |
|---|---|---|
| POST | `/targets/{target_id}/scans` | Start a `Scan` against a registered target (`status=running`) |
| POST | `/targets/{target_id}/pipeline` | Start the full n8n pipeline (Módulo 6) for a target — creates the `Scan` and triggers n8n's Webhook node; returns `202` immediately, before the pipeline finishes |
| GET | `/scans/{scan_id}` | Fetch one scan |
| POST | `/scans/{scan_id}/complete` | Mark a scan `completed`/`failed`, sets `finished_at` |
| POST | `/scans/{scan_id}/tasks` | Ingest a Scanner Service `RawScanResult` — creates the `ScanTask` row and, when the payload carries `parsed` output, normalizes it into `Service`/`Technology`/`Finding`/`CveReference` rows in one transaction |
| GET | `/scans/{scan_id}/findings` | List normalized findings for a scan, each with its CVE references |

## Endpoints (Módulo 7)

| Method | Path | Description |
|---|---|---|
| POST | `/scans/{scan_id}/reports?format=pdf\|html\|markdown\|json` | Gathers target/scan/findings and pushes them to the Reports Service to render; persists the resulting `Report` row |
| GET | `/scans/{scan_id}/reports` | List reports generated for a scan |
| GET | `/reports/{report_id}/download` | Proxies the rendered file from the Reports Service — the two services don't share a filesystem |

Interactive docs: `http://localhost:${BACKEND_PORT:-8000}/docs`.

## Report generation (Módulo 7)

`app/services/report_service.py::generate_report` is the only place that
talks to the Reports Service: it gathers a target, its scan, and every
finding (reusing `target_service`/`scan_service`/`finding_service`, no new
queries), serializes them with the same `TargetRead`/`ScanRead`/
`FindingRead` schemas the rest of the API already returns, and pushes the
whole thing to the Reports Service in one request. The Reports Service is
intentionally stateless (see [`reports/README.md`](../reports/README.md))
— it never queries Postgres or calls back into the Backend, so this is a
one-way push, not a pull.

## Normalization and severity classification (Módulo 5)

`POST /scans/{scan_id}/tasks` is the boundary where a tool-specific
`RawScanResult` (as returned by the Scanner Service, Módulo 4) becomes
normalized rows. `app/normalization/registry.py` maps `tool_name` to a
`normalize(parsed) -> NormalizedData` function — the same plugin pattern
as the Scanner Service's adapter registry, so adding normalization support
for a new tool is one file plus one registry line. Each normalizer only
returns plain dataclasses (`app/normalization/types.py`); persisting them
as ORM rows happens once, in `app/services/scan_task_service.py`.

Severity is computed per tool, since each gives a different signal
(`app/normalization/severity.py`):

- **Nuclei** carries its own `info`/`low`/`medium`/`high`/`critical` label
  per template match — trusted directly.
- **ZAP** carries a numeric `riskcode` ("0".."3") per alert, mapped
  directly rather than parsed out of the human-readable `riskdesc` string
  (e.g. `"High (Medium)"`).
- **Nikto** gives no severity or CVSS signal at all — every finding is
  conservatively set to `low`, flagged for manual triage rather than
  pre-triaged by risk.
- **Nmap** and **WhatWeb** don't produce findings: they feed the
  `services`/`technologies` tables instead (reconnaissance data, not
  vulnerabilities by themselves).

CVE mapping only happens for tools that report one: Nuclei's
`info.classification.cve-id` (list) becomes one `CveReference` row per CVE,
carrying the template's `cvss-score`/`cvss-metrics` alongside it. Nikto and
ZAP alerts reference CWEs, not CVEs, so they never produce `CveReference`
rows.

A scan_task whose normalizer raises (unexpected shape from a tool) doesn't
fail the ingest request — the raw result is still recorded, with the
normalization error appended to the scan_task's `error_message`, since the
raw output is valuable on its own even when it can't be turned into
structured findings.

## Running it

Part of the root `docker-compose.yml`; `docker compose up -d` builds and
starts it after `db` is healthy and `migrate` has applied the schema. To
work on it in isolation:

```bash
docker compose up -d db migrate backend
curl http://localhost:${BACKEND_PORT:-8000}/health
```

## Why `name`/`host` are immutable after creation

Allowing `host` to change after creation would mean re-running the
whitelist check on update as well as create, and `name` uniqueness would
need the same re-check — for a lab-scoped, low-cardinality resource like
`targets`, that complexity isn't worth it. If a target needs a different
host, delete it and register a new one.
