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

## The lab whitelist

`app/services/target_service.py::register_target` rejects any `host` not
present in `BACKEND_ALLOWED_LAB_HOSTS` (comma-separated env var, see
`.env.example`) with `422 Unprocessable Entity`. Clients cannot set
`is_lab_target` themselves — it's derived server-side from that check. This
is the enforcement point referenced in [`docs/lab.md`](../docs/lab.md):
network segmentation keeps the rest of the platform off `lab-network`, and
this whitelist keeps arbitrary hosts out of the `targets` table in the
first place.

## Endpoints (Módulo 3)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness + DB connectivity check (used by the Docker healthcheck) |
| GET | `/targets?is_active=` | List targets, optionally filtered |
| POST | `/targets` | Register a target (`name`, `host`, `description`) — `host` must be whitelisted |
| GET | `/targets/{id}` | Fetch one target |
| PATCH | `/targets/{id}` | Update `description` and/or `is_active` (name/host are immutable) |
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
