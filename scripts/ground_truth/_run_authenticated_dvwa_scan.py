"""One-off: run authenticated (Nikto+Nuclei+ZAP) scans against dvwa and
ingest the results, to re-measure recall/precision/F1 for Recomendación #5
(docs/independent-evaluation-report.md).

The n8n pipeline doesn't know about `options.authenticated` yet (it's an
opt-in capability on the Scanner Service, not the default pipeline
behavior — see the module docstring on scanner/app/services/dvwa_auth.py),
so this bypasses n8n entirely: it calls the Scanner Service directly for
each of the three tools that can act on an authenticated session, and
ingests each result into the Backend by hand, the same shape n8n's own
`Ingest: *` nodes send. Nmap/WhatWeb are skipped — they don't participate
in the ground-truth recall measurement (see their own build_command
docstrings on why authentication doesn't apply to them).

Run via: docker compose exec backend python scripts/ground_truth/_run_authenticated_dvwa_scan.py
"""

import json
import os
import sys
import uuid
from pathlib import Path

import httpx

BACKEND_URL = "http://localhost:8000"
SCANNER_URL = "http://scanner:8100"
BACKEND_HEADERS = {"X-API-Key": os.environ["BACKEND_API_KEY"]}
SCANNER_HEADERS = {"X-Internal-Token": os.environ["INTERNAL_API_KEY"]}

TARGET_HOST = "dvwa"
TOOLS = ["nikto", "nuclei", "zap"]


def main() -> None:
    name = f"ground-truth-dvwa-authenticated-{uuid.uuid4().hex[:8]}"
    create = httpx.post(
        f"{BACKEND_URL}/targets",
        json={"name": name, "host": TARGET_HOST, "description": "authenticated ground-truth run"},
        headers=BACKEND_HEADERS,
        timeout=15.0,
    )
    create.raise_for_status()
    target_id = create.json()["id"]

    try:
        scan_resp = httpx.post(
            f"{BACKEND_URL}/targets/{target_id}/scans",
            json={"triggered_by": "_run_authenticated_dvwa_scan.py"},
            headers=BACKEND_HEADERS,
            timeout=15.0,
        )
        scan_resp.raise_for_status()
        scan_id = scan_resp.json()["id"]
        print(f"Created scan {scan_id} against target {target_id} ({TARGET_HOST})")

        any_failed = False
        for tool in TOOLS:
            print(f"-- Running {tool} (authenticated) --")
            result = httpx.post(
                f"{SCANNER_URL}/scan/{tool}",
                json={
                    "target": TARGET_HOST,
                    "port": 80,
                    "scheme": "http",
                    "options": {"authenticated": True},
                },
                headers=SCANNER_HEADERS,
                timeout=920.0,
            )
            result.raise_for_status()
            raw = result.json()
            print(f"   status={raw['status']} error={raw.get('error_message')}")
            any_failed = any_failed or raw["status"] != "completed"

            ingest = httpx.post(
                f"{BACKEND_URL}/scans/{scan_id}/tasks",
                json={
                    "tool": raw["tool"],
                    "command": raw["command"],
                    "status": raw["status"],
                    "started_at": raw["started_at"],
                    "finished_at": raw["finished_at"],
                    "raw_output": raw["raw_output"],
                    "parsed": raw.get("parsed"),
                    "error_message": raw.get("error_message"),
                },
                headers=BACKEND_HEADERS,
                timeout=30.0,
            )
            ingest.raise_for_status()
            ingest_result = ingest.json()
            print(f"   ingested: {ingest_result['findings_created']} findings")

        complete = httpx.post(
            f"{BACKEND_URL}/scans/{scan_id}/complete",
            json={"status": "failed" if any_failed else "completed"},
            headers=BACKEND_HEADERS,
            timeout=15.0,
        )
        complete.raise_for_status()

        findings = httpx.get(
            f"{BACKEND_URL}/scans/{scan_id}/findings", headers=BACKEND_HEADERS, timeout=15.0
        ).json()
        tasks = httpx.get(
            f"{BACKEND_URL}/scans/{scan_id}/tasks", headers=BACKEND_HEADERS, timeout=15.0
        ).json()

        out_dir = Path(__file__).parent
        (out_dir / "sample_run_dvwa_authenticated_findings.json").write_text(
            json.dumps(findings, indent=2), encoding="utf-8"
        )
        (out_dir / "sample_run_dvwa_authenticated_tasks.json").write_text(
            json.dumps(tasks, indent=2), encoding="utf-8"
        )
        print(f"\nWrote {len(findings)} findings, {len(tasks)} tasks. scan_id={scan_id}")
        if any_failed:
            print("WARNING: at least one tool did not complete successfully.", file=sys.stderr)
            sys.exit(1)
    finally:
        httpx.delete(f"{BACKEND_URL}/targets/{target_id}", headers=BACKEND_HEADERS, timeout=15.0)


if __name__ == "__main__":
    main()
