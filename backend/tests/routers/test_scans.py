import os
import uuid

import httpx
from fastapi.testclient import TestClient

from app.main import app


def _create_target(client):
    response = client.post("/targets", json={"name": "juice-shop-demo", "host": "juice-shop"})
    return response.json()


def _create_scan(client, target_id):
    response = client.post(f"/targets/{target_id}/scans", json={})
    return response.json()


def test_list_scans_for_target_happy_path(client):
    # ix_scans_one_active_per_target allows only one non-terminal scan per
    # target - complete the first before creating the second, same as a
    # real sequential history would look.
    target = _create_target(client)
    first = client.post(f"/targets/{target['id']}/scans", json={}).json()
    client.post(f"/scans/{first['id']}/complete", json={"status": "completed"})
    client.post(f"/targets/{target['id']}/scans", json={})

    response = client.get(f"/targets/{target['id']}/scans")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_scans_for_target_empty(client):
    target = _create_target(client)
    response = client.get(f"/targets/{target['id']}/scans")
    assert response.status_code == 200
    assert response.json() == []


def test_list_scans_for_target_unknown_target_404(client):
    response = client.get(f"/targets/{uuid.uuid4()}/scans")
    assert response.status_code == 404


def test_list_scans_for_target_respects_limit_and_offset(client):
    target = _create_target(client)
    for _ in range(3):
        scan = client.post(f"/targets/{target['id']}/scans", json={}).json()
        client.post(f"/scans/{scan['id']}/complete", json={"status": "completed"})

    first_page = client.get(f"/targets/{target['id']}/scans", params={"limit": 2})
    assert first_page.status_code == 200
    assert len(first_page.json()) == 2

    second_page = client.get(f"/targets/{target['id']}/scans", params={"limit": 2, "offset": 2})
    assert second_page.status_code == 200
    assert len(second_page.json()) == 1


def test_complete_scan_happy_path(client):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    response = client.post(f"/scans/{scan['id']}/complete", json={"status": "completed"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["finished_at"] is not None


def test_complete_scan_with_failed_status_and_error_message(client):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    response = client.post(
        f"/scans/{scan['id']}/complete",
        json={"status": "failed", "error_message": "no HTTP service found"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["error_message"] == "no HTTP service found"


def test_complete_scan_twice_returns_409(client):
    # Regression (docs/independent-evaluation-report.md, Recomendación #6):
    # nothing used to stop a scan already in a terminal status from being
    # completed again, silently overwriting the first outcome.
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    first = client.post(f"/scans/{scan['id']}/complete", json={"status": "completed"})
    assert first.status_code == 200

    second = client.post(f"/scans/{scan['id']}/complete", json={"status": "failed"})
    assert second.status_code == 409


def test_complete_scan_unknown_scan_404(client):
    response = client.post(f"/scans/{uuid.uuid4()}/complete", json={"status": "completed"})
    assert response.status_code == 404


def test_list_findings_for_scan_happy_path(client):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])
    client.post(
        f"/scans/{scan['id']}/tasks",
        json={
            "tool": "nuclei",
            "command": "nuclei -u http://juice-shop:80",
            "status": "completed",
            "started_at": "2026-08-20T00:00:00Z",
            "finished_at": "2026-08-20T00:00:10Z",
            "raw_output": "",
            "parsed": [
                {
                    "template-id": "exposed-panel",
                    "type": "http",
                    "host": "juice-shop",
                    "info": {"name": "Exposed Admin Panel", "severity": "high"},
                }
            ],
        },
    )

    response = client.get(f"/scans/{scan['id']}/findings")
    assert response.status_code == 200
    findings = response.json()
    assert len(findings) == 1
    assert findings[0]["title"] == "Exposed Admin Panel"


def test_list_findings_for_scan_empty(client):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    response = client.get(f"/scans/{scan['id']}/findings")
    assert response.status_code == 200
    assert response.json() == []


def test_list_findings_for_scan_unknown_scan_404(client):
    response = client.get(f"/scans/{uuid.uuid4()}/findings")
    assert response.status_code == 404


def test_list_findings_for_scan_respects_limit_and_offset(client):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])
    client.post(
        f"/scans/{scan['id']}/tasks",
        json={
            "tool": "nuclei",
            "command": "nuclei -u http://juice-shop:80",
            "status": "completed",
            "started_at": "2026-08-20T00:00:00Z",
            "finished_at": "2026-08-20T00:00:10Z",
            "raw_output": "",
            "parsed": [
                {
                    "template-id": f"t{i}",
                    "type": "http",
                    "host": "juice-shop",
                    "info": {"name": f"Finding {i}", "severity": "low"},
                }
                for i in range(3)
            ],
        },
    )

    first_page = client.get(f"/scans/{scan['id']}/findings", params={"limit": 2})
    assert first_page.status_code == 200
    assert len(first_page.json()) == 2

    second_page = client.get(f"/scans/{scan['id']}/findings", params={"limit": 2, "offset": 2})
    assert second_page.status_code == 200
    assert len(second_page.json()) == 1


def test_list_scan_tasks_respects_limit_and_offset(client):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])
    for tool in ("nmap", "whatweb", "nikto"):
        client.post(
            f"/scans/{scan['id']}/tasks",
            json={
                "tool": tool,
                "command": f"{tool} ...",
                "status": "completed",
                "started_at": "2026-08-20T00:00:00Z",
                "finished_at": "2026-08-20T00:00:10Z",
                "raw_output": "",
                "parsed": None,
            },
        )

    first_page = client.get(f"/scans/{scan['id']}/tasks", params={"limit": 2})
    assert first_page.status_code == 200
    assert len(first_page.json()) == 2

    second_page = client.get(f"/scans/{scan['id']}/tasks", params={"limit": 2, "offset": 2})
    assert second_page.status_code == 200
    assert len(second_page.json()) == 1


def test_complete_scan_rejects_the_frontend_api_key_alone(client):
    # 5th independent evaluation: /scans/{id}/complete and /scans/{id}/tasks
    # used to share BACKEND_API_KEY with every Frontend-facing route, so
    # anyone holding the Frontend's key (which the Frontend necessarily
    # does) could force-complete a scan or forge its ingested tasks. They
    # now require the separate N8N_CALLBACK_API_KEY (X-N8N-Callback-Key)
    # instead - the Frontend's own X-API-Key must not be sufficient here.
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    frontend_only_client = TestClient(
        app, headers={"X-API-Key": os.environ["BACKEND_API_KEY"]}
    )
    response = frontend_only_client.post(
        f"/scans/{scan['id']}/complete", json={"status": "completed"}
    )
    assert response.status_code == 401


def test_ingest_scan_task_rejects_the_frontend_api_key_alone(client):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    frontend_only_client = TestClient(
        app, headers={"X-API-Key": os.environ["BACKEND_API_KEY"]}
    )
    response = frontend_only_client.post(
        f"/scans/{scan['id']}/tasks",
        json={
            "tool": "nmap",
            "command": "nmap ...",
            "status": "completed",
            "started_at": "2026-08-20T00:00:00Z",
            "finished_at": "2026-08-20T00:00:10Z",
            "raw_output": "",
            "parsed": None,
        },
    )
    assert response.status_code == 401


def test_targets_reject_the_n8n_callback_key_alone(client):
    # The reverse direction: the callback key must not double as a
    # Frontend-tier credential either.
    callback_only_client = TestClient(
        app, headers={"X-N8N-Callback-Key": os.environ["N8N_CALLBACK_API_KEY"]}
    )
    response = callback_only_client.post(
        "/targets", json={"name": "should-not-be-created", "host": "juice-shop"}
    )
    assert response.status_code == 401


def test_trigger_pipeline_router_wiring_happy_path(client, monkeypatch):
    # 6th independent evaluation: POST /targets/{id}/pipeline was only ever
    # exercised at the service layer (test_pipeline_service.py calls
    # pipeline_service.trigger_pipeline directly) - the route's own wiring
    # (202 status, response_model serialization, verify_api_key dependency)
    # was never driven through a real HTTP request, unlike every other
    # route in this router.
    class _FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResponse())

    target = _create_target(client)
    response = client.post(f"/targets/{target['id']}/pipeline")

    assert response.status_code == 202
    body = response.json()
    assert body["target_id"] == target["id"]
    assert body["status"] == "running"


def test_trigger_pipeline_unknown_target_404s(client):
    response = client.post(f"/targets/{uuid.uuid4()}/pipeline")
    assert response.status_code == 404
