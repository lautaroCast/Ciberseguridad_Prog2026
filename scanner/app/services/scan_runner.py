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
from app.services import dvwa_auth

# Only these three tools actually find vulnerabilities on authenticated
# pages (Nmap/WhatWeb don't operate at the application-auth layer — see
# their own build_command docstrings) — no point paying an extra HTTP
# round-trip against a target that won't use the cookie anyway.
_SUPPORTS_AUTH_COOKIE = {"nikto", "nuclei", "zap"}


def execute(
    adapter: ScannerAdapter,
    *,
    target: str,
    port: int,
    scheme: str,
    options: dict[str, Any],
    timeout: int,
) -> RawScanResult:
    started_at = datetime.now(UTC)

    auth_cookie: str | None = None
    if options.get("authenticated") and adapter.tool_name in _SUPPORTS_AUTH_COOKIE:
        # options={"authenticated": true} (Recomendación #5,
        # docs/independent-evaluation-report.md) — currently only DVWA's
        # login+security-level flow is implemented; a target without it
        # (e.g. juice-shop) fails this step and the scan is reported
        # failed rather than silently running unauthenticated.
        try:
            auth_cookie = dvwa_auth.get_authenticated_cookie(target, port=port, scheme=scheme)
        except Exception as exc:  # noqa: BLE001 — DvwaAuthError, network errors, etc.
            return RawScanResult(
                tool=adapter.tool_name,
                target=target,
                command="",
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                raw_output="",
                error_message=f"Authentication against {target} failed: {exc}",
            )

        # auth_cookie flows into 3 different adapters' argv (Nikto's
        # -Add-header, Nuclei's -H, ZAP's -config replacer value) — not the
        # same shape of risk `target`/`options` guard against (this is a
        # "name=value; name=value" cookie string, not a bare CLI token, so
        # a leading "-" check wouldn't protect anything real here), but an
        # embedded CR/LF has no legitimate reason to be in a session cookie
        # and could otherwise smuggle extra lines into whatever config/log
        # format each tool builds around this value. Checked once here
        # rather than in each of the 3 adapters separately.
        if auth_cookie is not None and ("\r" in auth_cookie or "\n" in auth_cookie):
            return RawScanResult(
                tool=adapter.tool_name,
                target=target,
                command="",
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                raw_output="",
                error_message=f"Authentication against {target} failed: session cookie contained an embedded newline",
            )

    output_path = ""
    if adapter.uses_output_file:
        fd, output_path = tempfile.mkstemp(suffix=adapter.output_file_extension)
        os.close(fd)
        # Some tools (ZAP) refuse to write to a path that already exists as
        # a zero-byte file; they expect to create it themselves.
        os.unlink(output_path)

    command = adapter.build_command(
        target=target,
        port=port,
        scheme=scheme,
        options=options,
        output_path=output_path,
        auth_cookie=auth_cookie,
    )
    command_str = " ".join(command)
    # The literal cookie value is known here (it's the same `auth_cookie`
    # passed into build_command above) - an exact substring replace catches
    # it regardless of which of the 3 adapters' argv shape embeds it
    # (Nikto's -Add-header, Nuclei's -H, ZAP's -config replacer value),
    # unlike a regex guessing at "Cookie: ..." that could miss a format
    # variant. `command` (the real argv used by subprocess.run below) is
    # left untouched - only the *persisted* string is redacted.
    if auth_cookie is not None:
        command_str = command_str.replace(auth_cookie, "[redacted]")

    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        # A killed tool may have already written partial output before the
        # timeout — clean it up here explicitly (the success path below
        # never runs, and this file is otherwise leaked forever). This
        # can't be a `finally` block: `output_path` is only ever truthy
        # when `adapter.uses_output_file` is True, so a `finally` that
        # also checks `uses_output_file` would run for every exit path,
        # including success, and would delete the file the success branch
        # still needs to read.
        if output_path and Path(output_path).exists():
            Path(output_path).unlink(missing_ok=True)
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
        if output_path and Path(output_path).exists():
            Path(output_path).unlink(missing_ok=True)
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
