from datetime import UTC, datetime

from app.schemas.scan import RawScanResult
from app.services import scan_runner


def _fake_result(**overrides) -> RawScanResult:
    defaults = dict(
        tool="nmap",
        target="juice-shop",
        command="nmap ...",
        status="completed",
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        raw_output="",
        parsed=[],
        error_message=None,
    )
    defaults.update(overrides)
    return RawScanResult(**defaults)


def test_get_tools_lists_all_five(client):
    response = client.get("/tools")
    assert response.status_code == 200
    assert sorted(response.json()) == sorted(["nmap", "whatweb", "nikto", "nuclei", "zap"])


def test_scan_unknown_tool_returns_404(client):
    response = client.post("/scan/unknown-tool", json={"target": "juice-shop"})
    assert response.status_code == 404
    assert "/tools" in response.json()["detail"]


def test_scan_target_validation(client):
    response = client.post("/scan/nmap", json={"target": ""})
    assert response.status_code == 422

    response = client.post("/scan/nmap", json={"target": "x" * 256})
    assert response.status_code == 422


def test_scan_port_validation(client):
    assert client.post("/scan/nmap", json={"target": "juice-shop", "port": 0}).status_code == 422
    assert (
        client.post("/scan/nmap", json={"target": "juice-shop", "port": 65536}).status_code == 422
    )


def test_scan_scheme_validation(client):
    response = client.post(
        "/scan/nmap", json={"target": "juice-shop", "scheme": "ftp"}
    )
    assert response.status_code == 422


def test_scan_timeout_seconds_validation(client):
    response = client.post(
        "/scan/nmap", json={"target": "juice-shop", "timeout_seconds": 0}
    )
    assert response.status_code == 422


def test_scan_happy_path(client, monkeypatch):
    monkeypatch.setattr(scan_runner, "execute", lambda *a, **k: _fake_result())
    response = client.post("/scan/nmap", json={"target": "juice-shop"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_timeout_omitted_uses_settings_max(client, monkeypatch):
    captured = {}

    def _fake_execute(adapter, *, target, port, scheme, options, timeout):
        captured["timeout"] = timeout
        return _fake_result()

    monkeypatch.setattr(scan_runner, "execute", _fake_execute)
    client.post("/scan/nmap", json={"target": "juice-shop"})

    from app.config import get_settings

    assert captured["timeout"] == get_settings().scanner_max_timeout_seconds


def test_timeout_above_max_is_capped(client, monkeypatch):
    captured = {}

    def _fake_execute(adapter, *, target, port, scheme, options, timeout):
        captured["timeout"] = timeout
        return _fake_result()

    monkeypatch.setattr(scan_runner, "execute", _fake_execute)

    from app.config import get_settings

    max_timeout = get_settings().scanner_max_timeout_seconds
    client.post(
        "/scan/nmap",
        json={"target": "juice-shop", "timeout_seconds": max_timeout + 500},
    )
    assert captured["timeout"] == max_timeout
