import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.adapters.nikto_adapter import NiktoAdapter
from app.adapters.nmap_adapter import NmapAdapter
from app.services import dvwa_auth, scan_runner


def _completed(stdout="", stderr="", returncode=0):
    return MagicMock(stdout=stdout, stderr=stderr, returncode=returncode)


def test_successful_stdout_adapter(monkeypatch):
    adapter = NmapAdapter()
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _completed(stdout="<nmaprun></nmaprun>")
    )
    result = scan_runner.execute(
        adapter, target="juice-shop", port=80, scheme="http", options={}, timeout=30
    )
    assert result.status == "completed"
    assert result.parsed == []  # NmapAdapter.parse_output of an empty <nmaprun/>
    assert result.error_message is None


def test_timeout_expired(monkeypatch):
    adapter = NmapAdapter()

    def _raise_timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd="nmap", timeout=30)

    monkeypatch.setattr(subprocess, "run", _raise_timeout)
    result = scan_runner.execute(
        adapter, target="juice-shop", port=80, scheme="http", options={}, timeout=30
    )
    assert result.status == "failed"
    assert "30s timeout" in result.error_message


def test_binary_not_found(monkeypatch):
    adapter = NmapAdapter()

    def _raise_not_found(*a, **k):
        raise FileNotFoundError("nmap: not found")

    monkeypatch.setattr(subprocess, "run", _raise_not_found)
    result = scan_runner.execute(
        adapter, target="juice-shop", port=80, scheme="http", options={}, timeout=30
    )
    assert result.status == "failed"
    assert "Tool binary not found" in result.error_message


def test_nonzero_exit_with_empty_output_fails(monkeypatch):
    adapter = NmapAdapter()
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _completed(stdout="", stderr="connection refused", returncode=1)
    )
    result = scan_runner.execute(
        adapter, target="juice-shop", port=80, scheme="http", options={}, timeout=30
    )
    assert result.status == "failed"
    assert "connection refused" in result.error_message


def test_nonzero_exit_with_output_still_completes(monkeypatch):
    # Many tools (nikto/nuclei/nmap) use a non-zero exit code to mean
    # "findings were found", not "crashed" — only empty output + non-zero
    # exit should be treated as a real failure.
    adapter = NmapAdapter()
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _completed(stdout="<nmaprun></nmaprun>", returncode=1)
    )
    result = scan_runner.execute(
        adapter, target="juice-shop", port=80, scheme="http", options={}, timeout=30
    )
    assert result.status == "completed"


def test_parse_error_does_not_fail_the_scan(monkeypatch):
    adapter = NmapAdapter()
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(stdout="not-valid-xml"))
    result = scan_runner.execute(
        adapter, target="juice-shop", port=80, scheme="http", options={}, timeout=30
    )
    assert result.status == "completed"
    assert result.parsed is None
    assert "failed to parse output" in result.error_message


def test_output_file_adapter_reads_from_file_not_stdout(monkeypatch, tmp_path):
    adapter = NiktoAdapter()
    written_path: dict[str, Path] = {}

    def _fake_run(command, capture_output, text, timeout):
        # Nikto's build_command places the output path right after "-output".
        output_path = Path(command[command.index("-output") + 1])
        assert not output_path.exists(), "scan_runner must unlink the pre-created temp file first"
        output_path.write_text('[{"vulnerabilities": []}]')
        written_path["value"] = output_path
        return _completed(stdout="this should be ignored")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = scan_runner.execute(
        adapter, target="juice-shop", port=80, scheme="http", options={}, timeout=30
    )
    assert result.status == "completed"
    assert result.raw_output == '[{"vulnerabilities": []}]'
    assert result.parsed == [{"vulnerabilities": []}]
    # scan_runner must have cleaned up the temp file afterwards.
    assert not written_path["value"].exists()


def test_output_file_adapter_cleans_up_partial_file_on_timeout(monkeypatch, tmp_path):
    # COD-3 regression: a killed Nikto/ZAP process may have already written
    # partial output to its temp file before the timeout fired — that file
    # must not be leaked on disk.
    adapter = NiktoAdapter()
    written_path: dict[str, Path] = {}

    def _fake_run(command, capture_output, text, timeout):
        output_path = Path(command[command.index("-output") + 1])
        output_path.write_text('{"partial": true')  # truncated, as if killed mid-write
        written_path["value"] = output_path
        raise subprocess.TimeoutExpired(cmd="nikto", timeout=timeout)

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = scan_runner.execute(
        adapter, target="juice-shop", port=80, scheme="http", options={}, timeout=30
    )
    assert result.status == "failed"
    assert not written_path["value"].exists()


def test_authenticated_option_fetches_cookie_and_passes_it_to_build_command(monkeypatch):
    # Recomendación #5 (docs/independent-evaluation-report.md).
    adapter = NiktoAdapter()
    captured_commands: list[list[str]] = []

    def _fake_run(command, capture_output, text, timeout):
        captured_commands.append(command)
        return _completed(stdout="")

    monkeypatch.setattr(
        dvwa_auth, "get_authenticated_cookie", lambda target, port, scheme: "security=low; PHPSESSID=abc"
    )
    monkeypatch.setattr(subprocess, "run", _fake_run)

    result = scan_runner.execute(
        adapter, target="dvwa", port=80, scheme="http", options={"authenticated": True}, timeout=30
    )
    # The real subprocess call must still carry the real cookie - the tool
    # itself needs it to actually authenticate.
    assert "Cookie: security=low; PHPSESSID=abc" in captured_commands[0]


def test_authenticated_option_redacts_the_cookie_from_the_persisted_command(monkeypatch):
    # 5th independent evaluation, backend+DB+scanner: the DVWA session
    # cookie used to be persisted verbatim in ScanTask.command and returned
    # unredacted by GET /scans/{id}/tasks.
    adapter = NiktoAdapter()
    monkeypatch.setattr(
        dvwa_auth, "get_authenticated_cookie", lambda target, port, scheme: "security=low; PHPSESSID=abc"
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(stdout=""))

    result = scan_runner.execute(
        adapter, target="dvwa", port=80, scheme="http", options={"authenticated": True}, timeout=30
    )
    assert "PHPSESSID=abc" not in result.command
    assert "Cookie: [redacted]" in result.command


def test_authenticated_option_ignored_for_tools_without_cookie_support(monkeypatch):
    adapter = NmapAdapter()
    calls = []
    monkeypatch.setattr(
        dvwa_auth,
        "get_authenticated_cookie",
        lambda target, port, scheme: calls.append(1) or "should-not-be-used",
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(stdout="<nmaprun></nmaprun>"))

    scan_runner.execute(
        adapter, target="dvwa", port=80, scheme="http", options={"authenticated": True}, timeout=30
    )
    assert calls == []  # nmap isn't in _SUPPORTS_AUTH_COOKIE — never even attempted


def test_authentication_failure_fails_the_scan_without_running_the_tool(monkeypatch):
    adapter = NiktoAdapter()

    def _raise(*a, **k):
        raise dvwa_auth.DvwaAuthError("login failed with status 500")

    monkeypatch.setattr(dvwa_auth, "get_authenticated_cookie", _raise)
    subprocess_calls = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess_calls.append(1))

    result = scan_runner.execute(
        adapter, target="dvwa", port=80, scheme="http", options={"authenticated": True}, timeout=30
    )
    assert result.status == "failed"
    assert "Authentication against dvwa failed" in result.error_message
    assert subprocess_calls == []  # the tool must never run against an unauthenticated session


def test_cookie_with_embedded_newline_fails_the_scan_without_running_the_tool(monkeypatch):
    adapter = NiktoAdapter()
    monkeypatch.setattr(
        dvwa_auth,
        "get_authenticated_cookie",
        lambda target, port, scheme: "security=low; PHPSESSID=abc\r\nX-Injected: evil",
    )
    subprocess_calls = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess_calls.append(1))

    result = scan_runner.execute(
        adapter, target="dvwa", port=80, scheme="http", options={"authenticated": True}, timeout=30
    )
    assert result.status == "failed"
    assert "embedded newline" in result.error_message
    assert subprocess_calls == []


def test_unauthenticated_option_never_calls_auth_helper(monkeypatch):
    adapter = NiktoAdapter()
    calls = []
    monkeypatch.setattr(
        dvwa_auth, "get_authenticated_cookie", lambda target, port, scheme: calls.append(1)
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(stdout=""))

    scan_runner.execute(
        adapter, target="dvwa", port=80, scheme="http", options={}, timeout=30
    )
    assert calls == []
