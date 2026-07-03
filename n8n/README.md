# n8n — pipeline orchestration (Módulo 6)

n8n's only job here is orchestration: every node in
[`workflows/vulnscan-pipeline.json`](workflows/vulnscan-pipeline.json) is an
HTTP call into the Backend (Módulo 3/5) or the Scanner Service (Módulo 4).
No business logic — whitelist enforcement, normalization, severity
classification — lives in n8n; all of that already exists as versioned
Python code and n8n just calls it in the right order. This keeps the
pipeline testable and portable: swapping n8n for another orchestrator later
would not require moving any logic, only re-wiring HTTP calls.

## The 12 pipeline stages, mapped to actual nodes

The architecture doc (`docs/architecture.md`) defines 12 conceptual stages.
Several of them collapse into a single node because earlier modules already
implement them as one atomic operation:

| # | Stage | Node(s) |
|---|---|---|
| 1 | Recepción del target | `Webhook Trigger` / `Form Trigger` |
| 2 | Validación | `Create Scan (Manual)` (manual path only — hits `POST /targets/{id}/scans`, which 404s/422s via the Backend's existing whitelist checks); the webhook path is pre-validated by the Backend before n8n is even called |
| 3 | Normalización del target | `Resolve Pipeline Context` |
| 4 | Reconocimiento | `Scan: Nmap` + `Ingest: Nmap` |
| 5 | Identificación de tecnologías | `Scan: WhatWeb` + `Ingest: WhatWeb` |
| 6 | Selección inteligente de herramientas | `Select HTTP Port` |
| 7 | Escaneo | `Scan: Nikto` / `Scan: Nuclei` / `Scan: ZAP` |
| 8-10 | Consolidación, clasificación, persistencia | Each `Ingest: *` node — `POST /scans/{id}/tasks` (Módulo 5) normalizes and persists in one transaction, so these three conceptual stages happen inside a single Backend call per tool |
| 11 | Generación de reporte | `Generate Report` — `POST /scans/{id}/reports?format=pdf` (Módulo 7) |
| 12 | Notificación | `Download Report` + `Send Report Email` (email delivery), `Pipeline Complete` (execution log) |

## Two triggers, one pipeline

```
Webhook Trigger ──────┐
  (called by Backend) ├──► Resolve Pipeline Context ──► ... rest of the chain
Form Trigger ──────────┘
  (manual/demo)
```

- **Webhook Trigger** (`POST /webhook/vulnscan-pipeline`) is the production
  path. The Backend's `POST /targets/{id}/pipeline` (see
  `backend/app/services/pipeline_service.py`) already validated the target,
  created the `Scan` row, and calls this webhook with
  `{scan_id, target_id, host}` in the body. The trigger responds
  immediately (`responseMode: onReceived`) — the Backend's call returns in
  well under a second regardless of how long the scan itself takes; poll
  `GET /scans/{id}` or `GET /scans/{id}/findings` for progress.
- **Form Trigger** exists for running the whole pipeline **without** the
  Backend or a frontend involved — useful for demos before Módulo 8
  (frontend) is done. Open the node's "Test URL"/"Production URL" in a
  browser, paste a `target_id` (get one from `GET /targets` on the
  Backend), submit, and watch the execution in n8n's UI. This branch does
  its own `POST /targets/{id}/scans` + `GET /targets/{id}` calls first
  (the Backend endpoints already existed from Módulo 5) since it has no
  pre-created `Scan` to work with.

Both branches converge at **Resolve Pipeline Context**, the only node that
has to figure out which trigger actually fired — it looks up whichever of
`Edit Fields - From Webhook` / `Edit Fields - From Manual` has run data,
using a `try`/`catch` around `$('NodeName')` since referencing a node with
no execution data throws in n8n. Every node after it can reference
`Resolve Pipeline Context` directly and unconditionally, since by that
point in the graph both branches have already merged.

## Tool selection and sequencing

`Select HTTP Port` reads **Nmap's own HTTP response** directly (not a
database query) and picks the first open port whose `service_name` looks
like HTTP(S), defaulting to the first open port found otherwise. If Nmap
found zero open ports, the node returns zero items, which stops every
downstream node automatically — this is the "selección inteligente de
herramientas" stage, deliberately kept simple per the architecture doc
rather than building a rules engine.

WhatWeb, Nikto, Nuclei and ZAP then run **sequentially**, not as parallel
branches — this keeps the workflow a single linear chain (straightforward
to read and debug from the editor), and ZAP's active scan alone typically
takes 3-5 minutes, dwarfing the other three combined either way. Running
them concurrently is a reasonable future enhancement, not a correctness
requirement.

Nikto and Nuclei are called with bounded options (`max_time: "90s"` and
`tags: "exposure,misconfig,tech,default-login"` respectively) to keep a
full pipeline run predictable for a demo; ZAP runs its default quick active
scan with no artificial bound, since cutting it short would defeat the
point of running it. These are workflow-level defaults, not tool
limitations — adjust the relevant `Scan: *` node's JSON body to change
them.

## Report generation

`Generate Report` (stage 11) calls the Backend's
`POST /scans/{id}/reports?format=pdf` (Módulo 7) after `Complete Scan`,
which gathers the target/scan/findings and pushes them to the Reports
Service for rendering. It runs with `continueOnFail: true` — a report
failure (e.g. the Reports Service being briefly unavailable) shouldn't
mask the fact that the scan itself already finished successfully;
`Pipeline Complete`'s message falls back to noting the failure rather than
crashing the whole execution. Other formats (`html`, `markdown`, `json`)
are available on the same Backend endpoint but aren't auto-generated by
the pipeline — call it directly for those.

## Email delivery (stage 12)

`Download Report` pulls the PDF's bytes from the Backend's
`GET /reports/{id}/download` as a binary file (`responseFormat: file`),
then `Send Report Email` attaches it and sends via n8n's built-in
Send Email node. Both run with `continueOnFail: true`, same reasoning as
`Generate Report` — a delivery failure doesn't invalidate the scan that
already completed.

This is wired for **[Ethereal Email](https://ethereal.email)**, a fake
SMTP service built for exactly this — it never delivers to a real inbox,
it just captures what was sent so you can view it on their site. Nothing
about credentials can live in the workflow JSON (they're secrets, and
n8n stores them separately, encrypted, outside of any exported workflow)
so this is the one piece of stage 12 that needs a manual, per-instance
setup step:

1. Go to <https://ethereal.email/create> and generate a throwaway
   account (no signup needed — it hands you a random inbox instantly).
2. In n8n, go to **Credentials → New → SMTP**, and fill in the host/port/
   user/password Ethereal gave you (host is `smtp.ethereal.email`, port
   `587`).
3. Open the **Send Report Email** node, select that credential, and
   **Publish** the workflow again for the change to take effect.
4. After a pipeline run, check the Ethereal inbox
   (<https://ethereal.email/messages>, same login) — the report PDF
   should be there as an attachment.

`toEmail` is hardcoded to a placeholder (`test@ethereal.email`) — with
Ethereal it doesn't matter what address you put there, since nothing is
ever actually delivered; change it in the node if you want the field to
read as something more meaningful for a demo.

## Running it

Part of the root `docker-compose.yml`; `docker compose up -d` starts n8n
after the Backend is healthy. n8n does **not** auto-import workflows on
boot — this is a deliberate, standard n8n limitation (there's no supported
"watch this folder" mechanism), so the workflow has to be imported once per
fresh `n8n-data` volume:

```bash
docker compose up -d n8n
docker compose exec n8n n8n import:workflow --input=/workflows/vulnscan-pipeline.json
```

Then open `http://localhost:${N8N_PORT:-5678}` (basic-auth credentials from
`.env`), find "VulnScan Pipeline" in the workflow list, and **activate it**
(the toggle in the top-right) — an inactive workflow's Webhook trigger
won't respond, and its Form trigger only has a "test" URL rather than a
stable one. Once active, either:

- trigger it for real via `POST /targets/{id}/pipeline` on the Backend, or
- open the Form Trigger node, copy its Production URL, and run it by hand.

## Why the trigger isn't exposed directly to the frontend/user

Per the architecture, the Backend is the platform's only public API
surface (`Frontend → Backend API → n8n → Scanner Service`). If the
frontend called n8n's webhook directly, n8n would become a second public
entry point with none of the Backend's validation in front of it — the
Form Trigger's manual path exists explicitly as a *developer/demo*
shortcut, not a production trigger, which is why it re-does the target
validation itself (via the same `POST /targets/{id}/scans` the Backend
already exposes) rather than skipping it.
