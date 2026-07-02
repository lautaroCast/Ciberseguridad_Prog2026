# Scanner Service

Stateless FastAPI service that runs the platform's scanning tools —
**Nmap**, **WhatWeb**, **Nikto**, **Nuclei**, **OWASP ZAP** — against lab
targets and returns their raw (and, where feasible, structured) output.
It's the only service that bridges `app-network` and `lab-network`: the
Backend/n8n call it over `app-network`; it's the one thing allowed to reach
the vulnerable apps on `lab-network`.

## The plugin pattern

```
app/adapters/base.py       ScannerAdapter interface every tool implements
app/adapters/*_adapter.py  One file per tool: build_command() + parse_output()
app/adapters/registry.py   Maps tool_name -> adapter instance
app/services/scan_runner.py Shared subprocess execution (timing, timeouts,
                             stdout-vs-output-file capture) — written once,
                             not duplicated per adapter
app/routers/scans.py       Generic POST /scan/{tool_name} — dispatches via
                             the registry, never needs a new route per tool
```

Adding a tool: write an adapter class implementing `build_command()` (argv
to run) and usually `parse_output()` (turn raw text into structured data),
register it in `registry.py`. Nothing else changes — no new router, no
changes to `scan_runner.py`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness (no DB — this service is stateless) |
| GET | `/tools` | Registered tool names, for callers that want to discover what's scannable |
| POST | `/scan/{tool_name}` | Run a scan. Body: `{"target": "juice-shop", "port": 3000, "scheme": "http", "options": {}}` |

`options` is tool-specific and documented in each adapter's docstring
(e.g. nuclei's `severity`/`tags`, nikto's `max_time`, nmap's `ports`).
Unknown keys are ignored, so a caller can pass one options dict across
different tools without per-tool branching.

Response shape (`RawScanResult`) mirrors the `scan_tasks` table from
Módulo 1 on purpose — Módulo 5's normalization layer consumes it almost
directly:

```json
{
  "tool": "nuclei",
  "target": "juice-shop",
  "command": "nuclei -u http://juice-shop:3000 -jsonl -silent -duc",
  "status": "completed",
  "started_at": "...",
  "finished_at": "...",
  "raw_output": "...",
  "parsed": [ /* tool-specific structured findings, or null if not parseable */ ],
  "error_message": null
}
```

## Why each tool is invoked the way it is

These aren't arbitrary CLI choices — every one was verified by hand against
a real Juice Shop container before being written into an adapter:

- **nmap**: `-oX -` (XML to stdout). Fast, streams cleanly.
- **whatweb**: `--log-json=- -q --color=never`. Without `-q --color=never`,
  WhatWeb's colorized human-readable report interleaves into the same
  stdout stream as the JSON, corrupting it.
- **nikto**: `-output <file>` (not stdout). `-output -` hangs producing
  nothing — nikto only writes a complete report to a real file once the
  scan finishes. `-maxtime` bounds the scan; nikto's full check suite
  otherwise runs far longer than useful for a lab target.
- **nuclei**: `-jsonl -silent -duc`. Templates are baked into the image at
  build time (a cold `-update-templates` run takes ~1 minute — this way no
  scan request pays that cost). `-duc` stops it phoning home to check for
  template updates on every run.
- **zap**: `-cmd -quickurl <url> -quickout <file>.json` (one-shot process,
  not a long-running daemon driven over its API — keeps ZAP consistent
  with every other adapter's lifecycle). A full spider + active scan takes
  several minutes even against a small app — that's inherent to active
  scanning, not a bug. `SCANNER_MAX_TIMEOUT_SECONDS` (900s default) is
  sized with that in mind.

## Timeouts

Every scan request may pass `timeout_seconds`; the effective timeout is
always `min(requested, SCANNER_MAX_TIMEOUT_SECONDS)` — a caller can ask for
less time, never more, than the service-wide ceiling.

## Running it

```bash
docker compose up -d scanner juice-shop dvwa
curl -X POST http://localhost:${SCANNER_PORT:-8100}/scan/whatweb \
  -H "Content-Type: application/json" \
  -d '{"target": "juice-shop", "port": 3000}'
```
