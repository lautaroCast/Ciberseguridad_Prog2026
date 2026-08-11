"""Real measurement campaign — fills in the thesis's Chapter 12 tables with
actual numbers instead of [COMPLETAR] markers (audit finding C-01).

Runs N=RUNS consecutive automated pipeline executions against a single lab
target (same pattern as scripts/integration_test.py: hits the Backend's
own public API from inside its own container), and for each run:

- Decomposes total pipeline wall time into "tool execution time" (sum of
  each scan_task's own started_at/finished_at — Nmap/WhatWeb/Nikto/Nuclei/
  ZAP, dominated by ZAP's active scan per thesis §11.6) vs. "orchestration
  time" (everything else: n8n's context-resolution/port-selection nodes,
  the ingestion round-trip after each tool, and report generation) — this
  is the audit's own C-07-recommended decomposition, used because H1 was
  rescoped (per user decision) to the orchestration-time component only,
  which is what automation actually eliminates. Tool execution time is a
  floor common to both a manual operator and this pipeline; orchestration
  time is what a human would otherwise spend consolidating, classifying
  and writing the report by hand.
- Aggregates severity distribution, both overall and per tool (per
  docs/security.md's documented severity-mapping bias — reporting only
  the aggregate would hide it).
- Captures host/tool versions programmatically (never hand-typed).

Run via: docker compose exec backend python scripts/measurement_campaign.py
Optional: TARGET_HOST=juice-shop RUNS=5 docker compose exec ...
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
import uuid
from datetime import datetime, UTC
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"
API_KEY = os.environ["BACKEND_API_KEY"]
HEADERS = {"X-API-Key": API_KEY}
POLL_INTERVAL_SECONDS = 15
PIPELINE_TIMEOUT_SECONDS = 900
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}

TARGET_HOST = os.environ.get("TARGET_HOST", "dvwa")
RUNS = int(os.environ.get("RUNS", "5"))

_SCAN_TOOLS = {"nmap", "whatweb", "nikto", "nuclei", "zap"}

_RESULTS_DIR = Path(__file__).parent / "measurement_campaign_results"


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


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


def run_pipeline(name: str, host: str, description: str) -> tuple[str, str, dict, list[dict], list[dict]]:
    """Creates a target, triggers the pipeline, polls to a terminal status,
    fetches scan/tasks/findings, and deletes the target regardless of
    outcome. Shared by this campaign and one-off ground-truth scan scripts
    (scripts/ground_truth/_run_juice_shop_scan.py) so the create/trigger/
    poll/fetch/cleanup flow against the Backend API lives in one place.
    """
    create = httpx.post(
        f"{BASE_URL}/targets",
        json={"name": name, "host": host, "description": description},
        headers=HEADERS,
        timeout=15.0,
    )
    create.raise_for_status()
    target_id = create.json()["id"]

    try:
        trigger = httpx.post(
            f"{BASE_URL}/targets/{target_id}/pipeline", headers=HEADERS, timeout=15.0
        )
        trigger.raise_for_status()
        scan_id = trigger.json()["id"]

        status = _poll_until_terminal(scan_id)

        scan = httpx.get(f"{BASE_URL}/scans/{scan_id}", headers=HEADERS, timeout=15.0).json()
        tasks = httpx.get(f"{BASE_URL}/scans/{scan_id}/tasks", headers=HEADERS, timeout=15.0).json()
        findings = httpx.get(
            f"{BASE_URL}/scans/{scan_id}/findings", headers=HEADERS, timeout=15.0
        ).json()

        return scan_id, status, scan, tasks, findings
    finally:
        httpx.delete(f"{BASE_URL}/targets/{target_id}", headers=HEADERS, timeout=15.0)


def _run_once(run_index: int) -> dict:
    name = f"measurement-{run_index}-{uuid.uuid4().hex[:8]}"
    scan_id, status, scan, tasks, findings = run_pipeline(
        name, TARGET_HOST, "measurement_campaign.py"
    )
    return _summarize_run(run_index, scan_id, status, scan, tasks, findings)


def _summarize_run(
    run_index: int, scan_id: str, status: str, scan: dict, tasks: list[dict], findings: list[dict]
) -> dict:
    pipeline_start = _parse_dt(scan.get("started_at"))
    pipeline_end = _parse_dt(scan.get("finished_at"))
    pipeline_total_seconds = (
        (pipeline_end - pipeline_start).total_seconds()
        if pipeline_start and pipeline_end
        else None
    )

    tool_durations: dict[str, float] = {}
    for task in tasks:
        if task["tool_name"] not in _SCAN_TOOLS:
            continue
        start = _parse_dt(task.get("started_at"))
        end = _parse_dt(task.get("finished_at"))
        if start and end:
            tool_durations[task["tool_name"]] = (end - start).total_seconds()

    tool_execution_seconds = sum(tool_durations.values())
    orchestration_seconds = (
        pipeline_total_seconds - tool_execution_seconds
        if pipeline_total_seconds is not None
        else None
    )

    tool_by_task_id = {t["id"]: t["tool_name"] for t in tasks}
    severity_overall: dict[str, int] = {}
    severity_by_tool: dict[str, dict[str, int]] = {}
    for f in findings:
        sev = f["severity"]
        severity_overall[sev] = severity_overall.get(sev, 0) + 1
        tool = tool_by_task_id.get(f["scan_task_id"], "unknown")
        severity_by_tool.setdefault(tool, {})
        severity_by_tool[tool][sev] = severity_by_tool[tool].get(sev, 0) + 1

    return {
        "run_index": run_index,
        "scan_id": scan_id,
        "target_host": TARGET_HOST,
        "status": status,
        "pipeline_total_seconds": pipeline_total_seconds,
        "tool_execution_seconds": tool_execution_seconds,
        "orchestration_seconds": orchestration_seconds,
        "tool_durations_seconds": tool_durations,
        "findings_count": len(findings),
        "severity_distribution_overall": severity_overall,
        "severity_distribution_by_tool": severity_by_tool,
    }


def _capture_environment() -> dict:
    """Host spec + tool versions, captured programmatically — never
    hand-typed (audit A-11/A-12: both were left as [COMPLETAR]/[versión])."""

    def _sh(cmd: list[str]) -> str:
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, timeout=15
            ).stdout.strip()
        except Exception as exc:  # noqa: BLE001 — best-effort capture, not test-critical
            return f"<capture failed: {exc}>"

    # The backend container has no `docker` CLI, so `docker --version` run
    # from in here always fails — that CLI only exists on the host. The
    # host-side wrapper (scripts/run_measurement_campaign.sh) captures it
    # there and passes it through as env vars before `docker compose exec`.
    # Falling back to _sh() only helps if this script is ever run directly
    # on the host instead of inside the container.
    docker_version = os.environ.get("HOST_DOCKER_VERSION") or _sh(
        ["docker", "--version"]
    )
    docker_compose_version = os.environ.get("HOST_DOCKER_COMPOSE_VERSION") or _sh(
        ["docker", "compose", "version"]
    )
    # Same reasoning as the docker_version fields above: CPU/RAM/disk/OS are
    # host-level facts this script can't introspect from inside a container.
    # scripts/run_measurement_campaign.sh captures them on the host (audit
    # A-11 — the thesis's §9.4 host-spec table was left as [COMPLETAR]) and
    # passes them through as env vars. No fallback here (unlike docker_version)
    # because there's no in-container equivalent command to attempt.
    host_cpu = os.environ.get("HOST_CPU", "<not captured>")
    host_ram_gb = os.environ.get("HOST_RAM_GB", "<not captured>")
    host_disk_gb = os.environ.get("HOST_DISK_GB", "<not captured>")
    host_os = os.environ.get("HOST_OS", "<not captured>")

    # Same pattern again: the backend container has no route to `docker
    # compose exec scanner ...`, so the host wrapper runs each tool's own
    # `--version`/equivalent against the live Scanner container and passes
    # the output through. Nuclei's *template set* version is captured
    # separately from its engine version (audit A-12 specifically flags that
    # the template/signature date is what makes a scan run replicable, not
    # just the binary version — nuclei's own `-tv` flag reports it).
    scanner_tool_versions = {
        "nmap": os.environ.get("HOST_NMAP_VERSION", "<not captured>"),
        "whatweb": os.environ.get("HOST_WHATWEB_VERSION", "<not captured>"),
        "nikto": os.environ.get("HOST_NIKTO_VERSION", "<not captured>"),
        "nuclei_engine": os.environ.get("HOST_NUCLEI_VERSION", "<not captured>"),
        "nuclei_templates": os.environ.get("HOST_NUCLEI_TEMPLATES_VERSION", "<not captured>"),
        "zap": os.environ.get("HOST_ZAP_VERSION", "<not captured>"),
    }

    return {
        "captured_at": datetime.now(UTC).isoformat(),
        "docker_version": docker_version,
        "docker_compose_version": docker_compose_version,
        "host_cpu": host_cpu,
        "host_ram_gb": host_ram_gb,
        "host_disk_gb": host_disk_gb,
        "host_os": host_os,
        "scanner_tool_versions": scanner_tool_versions,
        "note": (
            "Scanner tool versions captured live from the running Scanner "
            "container (docker compose exec scanner ...), not from the "
            "Dockerfile pins — nuclei's binary is downloaded from GitHub's "
            "`latest` release at build time and its template set is updated "
            "at build time too, so neither is actually pinned to a fixed "
            "version; the only reproducible record is what was running "
            "during this campaign."
        ),
    }


def _write_outputs(runs: list[dict], environment: dict) -> None:
    _RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path = _RESULTS_DIR / f"{timestamp}.json"
    summary_path = _RESULTS_DIR / f"{timestamp}_summary.md"

    completed_runs = [r for r in runs if r["status"] == "completed"]
    pipeline_totals = [r["pipeline_total_seconds"] for r in completed_runs if r["pipeline_total_seconds"]]
    tool_totals = [r["tool_execution_seconds"] for r in completed_runs]
    orch_totals = [r["orchestration_seconds"] for r in completed_runs if r["orchestration_seconds"] is not None]

    def _stats(values: list[float]) -> dict:
        if not values:
            return {"mean": None, "stdev": None, "cv_pct": None}
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0.0
        return {
            "mean": round(mean, 2),
            "stdev": round(stdev, 2),
            "cv_pct": round(100 * stdev / mean, 1) if mean else None,
        }

    raw_path.write_text(
        json.dumps(
            {"target_host": TARGET_HOST, "runs": runs, "environment": environment}, indent=2
        ),
        encoding="utf-8",
    )

    lines = [
        f"# Campaña de medición — {TARGET_HOST} — {timestamp}",
        "",
        f"{len(completed_runs)}/{len(runs)} corridas completadas.",
        "",
        "## Entorno",
        "",
        f"- Docker: {environment['docker_version']}",
        f"- Docker Compose: {environment['docker_compose_version']}",
        f"- CPU: {environment['host_cpu']}",
        f"- RAM: {environment['host_ram_gb']} GB",
        f"- Disco (C:): {environment['host_disk_gb']} GB",
        f"- SO: {environment['host_os']}",
        f"- Nmap: {environment['scanner_tool_versions']['nmap']}",
        f"- WhatWeb: {environment['scanner_tool_versions']['whatweb']}",
        f"- Nikto: {environment['scanner_tool_versions']['nikto']}",
        f"- Nuclei (motor): {environment['scanner_tool_versions']['nuclei_engine']}",
        f"- Nuclei (plantillas): {environment['scanner_tool_versions']['nuclei_templates']}",
        f"- ZAP: {environment['scanner_tool_versions']['zap']}",
        f"- {environment['note']}",
        "",
        "## Tiempos (segundos)",
        "",
        "| Corrida | Total pipeline | Ejecución de herramientas | Orquestación (H1) | Estado |",
        "|---|---|---|---|---|",
    ]
    for r in runs:
        lines.append(
            f"| {r['run_index']} | {r['pipeline_total_seconds']} | "
            f"{r['tool_execution_seconds']} | {r['orchestration_seconds']} | {r['status']} |"
        )
    pt = _stats(pipeline_totals)
    tt = _stats(tool_totals)
    ot = _stats(orch_totals)
    lines += [
        f"| **Media** | {pt['mean']} | {tt['mean']} | {ot['mean']} | — |",
        f"| **Desv. estándar** | {pt['stdev']} | {tt['stdev']} | {ot['stdev']} | — |",
        f"| **Coef. de variación (%)** | {pt['cv_pct']} | {tt['cv_pct']} | {ot['cv_pct']} | — |",
        "",
        "## H1 reformulada",
        "",
        "H1 original (auditoría, no contrastable sin brazo manual cronometrado) fue "
        "reemplazada por la recomendación C-07 del propio auditor: descomponer el "
        "tiempo en 'ejecución de herramientas' (piso común a cualquier operador, "
        "manual o automatizado — dominado por ZAP) vs. 'orquestación' (lo que la "
        "automatización elimina realmente: resolución de contexto, selección de "
        "puerto, ingesta/normalización entre herramientas, generación del reporte). "
        f"El componente de orquestación mide **{ot['mean']} s de media** "
        f"(CV {ot['cv_pct']}%) — ver docs/audit-corrections/ para la redacción final.",
        "",
        "## Distribución de severidad por herramienta",
        "",
    ]
    for r in runs:
        lines.append(f"### Corrida {r['run_index']} ({r['scan_id']})")
        lines.append("")
        lines.append(f"Agregado: `{r['severity_distribution_overall']}`")
        lines.append("")
        for tool, dist in r["severity_distribution_by_tool"].items():
            lines.append(f"- `{tool}`: `{dist}`")
        lines.append("")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {raw_path}")
    print(f"Wrote {summary_path}")


def main() -> None:
    print(f"== Measurement campaign: {RUNS} runs against '{TARGET_HOST}' ==")
    environment = _capture_environment()
    runs: list[dict] = []
    try:
        for i in range(1, RUNS + 1):
            print(f"\n-- Run {i}/{RUNS} --")
            runs.append(_run_once(i))
    finally:
        # Write whatever runs completed even if a later one raises, so a
        # transient failure on run N doesn't discard runs 1..N-1.
        if runs:
            _write_outputs(runs, environment)

    failed = [r for r in runs if r["status"] != "completed"]
    if len(runs) < RUNS or failed:
        print(
            f"\n{len(runs)}/{RUNS} run(s) finished, {len(failed)} did not complete.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("\nAll runs completed.")


if __name__ == "__main__":
    main()
