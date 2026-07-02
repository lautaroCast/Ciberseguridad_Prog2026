# Lab — vulnerable target applications

Defines the local, isolated laboratory that the platform is allowed to scan.
See [`docs/lab.md`](../docs/lab.md) for the legal/ethical scope; this file
covers the technical details of each target.

## Targets

### Juice Shop (`juice-shop`)

Official OWASP Juice Shop image (`bkimminich/juice-shop`), distroless —
no shell or package manager inside the container. It needs no setup step;
the healthcheck in `docker-compose.yml` calls Node's own `http` module
directly (`CMD` exec form) since there is no `curl`/`wget` to shell out to.

- URL: `http://localhost:${JUICE_SHOP_PORT:-3000}`

### DVWA (`dvwa`)

`vulnerables/web-dvwa`, an all-in-one Apache + MySQL + PHP image. DVWA
ships with an **empty database** — normally you open `setup.php` in a
browser and click "Create / Reset Database" by hand. That's a manual step
we can't allow, so `dvwa-init/` automates it.

- URL: `http://localhost:${DVWA_PORT:-3001}`
- Default credentials after init: `admin` / `password`
- Default security level baked into the image: `low`

#### `dvwa-init/`

A one-shot container (`restart: "no"`, `depends_on: dvwa: condition:
service_healthy`) that replays the exact HTTP request the "Create / Reset
Database" button sends:

1. `GET /setup.php` → captures the session cookie and the CSRF `user_token`
   DVWA embeds in the form.
2. `POST /setup.php` with `create_db` + the same `user_token` and cookie.
3. `GET /setup.php` again and greps the response for `Setup successful` to
   confirm the tables were actually created (a 302 redirect alone doesn't
   guarantee success — DVWA redirects to the same page on both outcomes).

Retries every `SLEEP_SECONDS` (default 5s) up to `MAX_ATTEMPTS` (default 30)
in case MySQL inside the DVWA container is still starting when Apache
already answers healthchecks. Re-running it against an already-initialized
database is safe: DVWA's setup routine always drops and recreates the
schema.

## Isolation

Both services attach only to `lab-network`. `app-network` services
(frontend, n8n, backend, db) have no route to `lab-network` at all — only
the Scanner Service (Módulo 4) bridges both networks. Host port publishing
(`JUICE_SHOP_PORT`, `DVWA_PORT`) works normally for local browser/scanner
access.

`lab-network` is intentionally **not** `internal: true`. That flag would
also stop the lab containers from reaching the internet, which looked like
a nice extra safety layer — but Docker silently skips host port publishing
for containers whose only network is internal (confirmed empirically: with
`internal: true`, `docker port` returned nothing and the app was
unreachable from the host despite a correct `ports:` entry). The platform's
actual safety guarantee — never scanning anything outside this lab — comes
from the Backend's target whitelist (Módulo 3), not from network egress
rules. See [`docs/lab.md`](../docs/lab.md).

## Adding another vulnerable app later

1. Add the image as a new service on `lab-network` in `docker-compose.yml`.
2. If it needs a setup step like DVWA's, add a sibling `<app>-init/`
   directory following the same pattern as `dvwa-init/`.
3. Register it as a `Target` row (Módulo 3) with `is_lab_target = true` so
   the Backend's whitelist accepts it.

No changes to the network topology, the Scanner Service, or the pipeline are
required.
