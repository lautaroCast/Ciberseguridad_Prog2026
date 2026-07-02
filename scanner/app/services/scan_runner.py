"""Shared subprocess execution for every adapter.

This is what makes the plugin pattern work: timing, timeout handling,
missing-binary handling, and stdout-vs-output-file capture live here once,
so an adapter is only ever "build this argv" (+ optionally "parse this
output") and nothing else.
"""

import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.adapters.base import ScannerAdapter
from app.schemas.scan import RawScanResult


def execute(
    adapter: ScannerAdapter,
    *,
    target: str,
    port: int,
    scheme: str,
    options: dict[str, Any],
    timeout: int,
) -> RawScanResult:
    output_path = ""
    if adapter.uses_output_file:
        fd, output_path = tempfile.mkstemp(suffix=adapter.output_file_extension)
        os.close(fd)
        # Some tools (ZAP) refuse to write to a path that already exists as
        # a zero-byte file; they expect to create it themselves.
        os.unlink(output_path)

    command = adapter.build_command(
        target=target, port=port, scheme=scheme, options=options, output_path=output_path
    )
    command_str = " ".join(command)
    started_at = datetime.now(UTC)

    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return RawScanResult(
            tool=adapter.tool_name,
            target=target,
            command=command_str,
            status="failed",
            started_at=started_at,
            finished_at=datetime.now(UTC),
            raw_output="",
            error_message=f"Scan exceeded the {timeout}s timeout and was terminated.",
        )
    except FileNotFoundError as exc:
        return RawScanResult(
            tool=adapter.tool_name,
            target=target,
            command=command_str,
            status="failed",
            started_at=started_at,
            finished_at=datetime.now(UTC),
            raw_output="",
            error_message=f"Tool binary not found: {exc}",
        )
    finally:
        if output_path and Path(output_path).exists() and not adapter.uses_output_file:
            # Defensive cleanup only; adapters that don't use an output
            # file never see this path created in the first place.
            Path(output_path).unlink(missing_ok=True)

    if adapter.uses_output_file:
        raw_output = Path(output_path).read_text() if Path(output_path).exists() else ""
        Path(output_path).unlink(missing_ok=True)
    else:
        raw_output = proc.stdout

    finished_at = datetime.now(UTC)

    # Many security tools use a non-zero exit code to mean "findings were
    # found", not "the tool crashed" (nikto, nuclei, nmap all do this in
    # various situations). Only treat the run as failed when there's BOTH
    # no output AND a non-zero exit — that combination means something
    # actually went wrong (e.g. connection refused, invalid target).
    if not raw_output.strip() and proc.returncode != 0:
        error_message = (
            proc.stderr.strip()[-2000:]
            if proc.stderr and proc.stderr.strip()
            else f"{adapter.tool_name} exited with code {proc.returncode} and produced no output."
        )
        return RawScanResult(
            tool=adapter.tool_name,
            target=target,
            command=command_str,
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            raw_output=raw_output,
            error_message=error_message,
        )

    parsed: Any | None = None
    parse_error: str | None = None
    try:
        parsed = adapter.parse_output(raw_output)
    except Exception as exc:  # noqa: BLE001 — a bad parse shouldn't 500 the request
        parse_error = f"Scan completed but failed to parse output: {exc}"

    return RawScanResult(
        tool=adapter.tool_name,
        target=target,
        command=command_str,
        status="completed",
        started_at=started_at,
        finished_at=finished_at,
        raw_output=raw_output,
        parsed=parsed,
        error_message=parse_error,
    )
