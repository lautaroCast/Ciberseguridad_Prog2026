import uuid


def _create_target(client):
    response = client.post("/targets", json={"name": "juice-shop-demo", "host": "juice-shop"})
    return response.json()


def _create_scan(client, target_id):
    response = client.post(f"/targets/{target_id}/scans", json={})
    return response.json()


def test_list_scans_for_target_happy_path(client):
    target = _create_target(client)
    client.post(f"/targets/{target['id']}/scans", json={})
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
