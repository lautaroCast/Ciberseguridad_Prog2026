# Database — schema & migrations

Single source of truth for the platform's PostgreSQL schema: SQLAlchemy
models under `models/` and Alembic migrations under `migrations/`. No other
service defines or duplicates the schema — the Backend API (Módulo 3) reuses
these same model classes rather than redefining them.

## Layout

```
models/        SQLAlchemy 2.0 declarative models (one file per table)
migrations/    Alembic environment + versioned migration scripts
alembic.ini    Alembic config (reads DATABASE_URL from the environment)
Dockerfile     Minimal image whose only job is `alembic upgrade head`
```

## How it runs

The root `docker-compose.yml` defines a one-shot `migrate` service built from
this directory. It waits for `db` to be healthy, runs `alembic upgrade head`,
and exits — `docker compose up -d` applies the schema automatically, no
manual step required. Any service that depends on the schema (e.g. `backend`)
declares `depends_on: migrate: condition: service_completed_successfully`.

To run it manually:

```bash
docker compose run --rm migrate            # upgrade to latest
docker compose run --rm migrate downgrade base   # tear down (dev only)
```

## Adding a migration

1. Edit/add a model under `models/`.
2. Regenerate the image and autogenerate a revision against a running `db`:

   ```bash
   docker compose build migrate
   docker compose run --rm migrate revision --autogenerate -m "describe the change"
   ```

3. **Read the generated file under `migrations/versions/` before committing.**
   Alembic autogenerate is a starting point, not a guarantee — it can miss
   constraint renames, data migrations, or enum value changes.
4. Apply it locally (`docker compose run --rm migrate`) to confirm it runs
   cleanly, then commit the migration file alongside the model change.

## Design notes

- **UUID primary keys** (`gen_random_uuid()`, built into PostgreSQL 16 core —
  no extension required) instead of serial integers, so IDs are safe to
  expose through the API without leaking row counts.
- **Two extensibility escape hatches are plain strings, not enums**:
  `scan_tasks.tool_name` and `findings.finding_type`. New scanner adapters or
  finding categories are additive at the application layer; only genuinely
  closed vocabularies (`scan_status`, `severity_level`, `report_format`,
  `user_role`) are modeled as native PostgreSQL enums.
- **`cve_references` is its own table**, not a column on `findings`, because
  a single finding (e.g. an outdated library flagged by Nuclei) can map to
  multiple CVEs.
- See [`docs/database.md`](../docs/database.md) for the full ER diagram and
  a description of every table.
