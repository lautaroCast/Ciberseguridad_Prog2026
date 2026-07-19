import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.adapters.nikto_adapter import NiktoAdapter
from app.adapters.nmap_adapter import NmapAdapter
from app.services import scan_runner


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
