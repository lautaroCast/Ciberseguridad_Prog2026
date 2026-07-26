"""End-to-end integration test — runs a real pipeline against real services.

Unlike the pytest suites (SQLite + mocks), this hits the Backend's own
public API from inside its own container, which in turn drives the real
n8n pipeline, the real Scanner Service (Nmap/WhatWeb/Nikto/Nuclei/ZAP)
against the real `dvwa` lab target, and the real Reports Service. It's
slow (minutes, dominated by ZAP's active scan) and not meant to run on
every save — see scripts/test-e2e.sh.

Run via: docker compose exec backend python scripts/integration_test.py
(needs BACKEND_API_KEY in its own environment, which it already has).
"""

import os
import sys
import time
import uuid

import httpx

BASE_URL = "http://localhost:8000"
API_KEY = os.environ["BACKEND_API_KEY"]
HEADERS = {"X-API-Key": API_KEY}
POLL_INTERVAL_SECONDS = 15
PIPELINE_TIMEOUT_SECONDS = 900
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}
REPORT_FORMATS = ["pdf", "html", "markdown", "json"]

_failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        print(f"  OK   {message}")
    else:
        print(f"  FAIL {message}")
        _failures.append(message)


def run_happy_path() -> None:
    print("== Happy path: full pipeline against dvwa ==")
    name = f"e2e-check-{uuid.uuid4().hex[:8]}"
    create = httpx.post(
        f"{BASE_URL}/targets",
        json={"name": name, "host": "dvwa", "description": "integration_test.py"},
        headers=HEADERS,
        timeout=15.0,
    )
    check(create.status_code == 201, f"create target -> 201 (got {create.status_code})")
    target_id = create.json()["id"]

    try:
        trigger = httpx.post(
            f"{BASE_URL}/targets/{target_id}/pipeline", headers=HEADERS, timeout=15.0
        )
        check(trigger.status_code == 202, f"trigger pipeline -> 202 (got {trigger.status_code})")
        scan_id = trigger.json()["id"]

        status = _poll_until_terminal(scan_id)
        check(status == "completed", f"scan reaches 'completed' (got '{status}')")

        findings = httpx.get(
            f"{BASE_URL}/scans/{scan_id}/findings", headers=HEADERS, timeout=15.0
        ).json()
        check(len(findings) > 0, f"findings not empty (got {len(findings)})")

        for fmt in REPORT_FORMATS:
            _check_report_format(scan_id, fmt)
    finally:
        httpx.delete(f"{BASE_URL}/targets/{target_id}", headers=HEADERS, timeout=15.0)


def _poll_until_terminal(scan_id: str) -> str:
    deadline = time.monotonic() + PIPELINE_TIMEOUT_SECONDS
    status = "pending"
    while time.monotonic() < deadline:
        response = httpx.get(f"{BASE_URL}/scans/{scan_id}", headers=HEADERS, timeout=15.0)
        status = response.json()["status"]
        print(f"  ... scan {scan_id} status={status}")
        if status in TERMINAL_STATUSES:
            return status
        time.sleep(POLL_INTERVAL_SECONDS)
    return status


def _check_report_format(scan_id: str, fmt: str) -> None:
    created = httpx.post(
        f"{BASE_URL}/scans/{scan_id}/reports",
        params={"format": fmt},
        headers=HEADERS,
        timeout=60.0,
    )
    check(created.status_code == 201, f"generate {fmt} report -> 201 (got {created.status_code})")
    report_id = created.json()["id"]

    downloaded = httpx.get(
        f"{BASE_URL}/reports/{report_id}/download", headers=HEADERS, timeout=30.0
    )
    check(downloaded.status_code == 200, f"download {fmt} report -> 200")

    if fmt == "pdf":
        check(downloaded.content.startswith(b"%PDF"), "pdf content starts with %PDF")
    elif fmt == "json":
        import json

        try:
            json.loads(downloaded.content)
            check(True, "json content parses")
        except ValueError:
            check(False, "json content parses")
    elif fmt == "html":
        check(b"<html" in downloaded.content.lower(), "html content contains <html")
    elif fmt == "markdown":
        check(len(downloaded.content) > 0, "markdown content not empty")


def run_error_paths() -> None:
    print("== Error paths ==")

    disallowed = httpx.post(
        f"{BASE_URL}/targets",
        json={"name": f"e2e-bad-host-{uuid.uuid4().hex[:8]}", "host": "evil.example.com"},
        headers=HEADERS,
        timeout=15.0,
    )
    check(
        disallowed.status_code == 422,
        f"non-whitelisted host -> 422 (got {disallowed.status_code})",
    )

    malformed = httpx.get(f"{BASE_URL}/targets/not-a-uuid", headers=HEADERS, timeout=15.0)
    check(malformed.status_code == 422, f"malformed uuid -> 422 (got {malformed.status_code})")

    missing = httpx.get(f"{BASE_URL}/targets/{uuid.uuid4()}", headers=HEADERS, timeout=15.0)
    check(missing.status_code == 404, f"unknown target -> 404 (got {missing.status_code})")


def main() -> None:
    run_error_paths()
    run_happy_path()

    print()
    if _failures:
        print(f"{len(_failures)} check(s) failed:")
        for message in _failures:
            print(f"  - {message}")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
