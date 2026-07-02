# Backend — API core

FastAPI service that owns the schema (reuses [`database/models`](../database/models)
verbatim, see [`Dockerfile`](Dockerfile)) and exposes the platform's REST API.
This module ships target registration; scans, findings and reports are
added in later modules against the same layering.

## Layout

```
app/
  main.py              FastAPI app, CORS, router registration
  config.py             Settings from environment variables (pydantic-settings)
  database.py            SQLAlchemy engine/session, get_db() dependency
  routers/                HTTP layer — request/response only, no business logic
  services/                Business rules (e.g. the lab whitelist)
  repositories/             Plain DB queries, no rules
  schemas/                   Pydantic request/response models
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

Interactive docs: `http://localhost:${BACKEND_PORT:-8000}/docs`.

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
