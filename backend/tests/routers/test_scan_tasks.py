import uuid
from datetime import UTC, datetime


def _create_target(client):
    response = client.post("/targets", json={"name": "juice-shop-demo", "host": "juice-shop"})
    return response.json()


def _create_scan(client, target_id):
    response = client.post(f"/targets/{target_id}/scans", json={})
    return response.json()


def _ingest_task(client, scan_id, tool="nmap"):
    started = datetime.now(UTC).isoformat()
    finished = datetime.now(UTC).isoformat()
    return client.post(
        f"/scans/{scan_id}/tasks",
        json={
            "tool": tool,
            "command": f"{tool} ...",
            "status": "completed",
            "started_at": started,
            "finished_at": finished,
            "raw_output": "",
            "parsed": None,
        },
    )


def test_list_scan_tasks_happy_path(client):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])
    _ingest_task(client, scan["id"], tool="nmap")
    _ingest_task(client, scan["id"], tool="whatweb")

    response = client.get(f"/scans/{scan['id']}/tasks")
    assert response.status_code == 200
    tools = sorted(task["tool_name"] for task in response.json())
    assert tools == ["nmap", "whatweb"]


def test_list_scan_tasks_includes_timestamps(client):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])
    _ingest_task(client, scan["id"], tool="nmap")

    response = client.get(f"/scans/{scan['id']}/tasks")
    task = response.json()[0]
    assert task["started_at"] is not None
    assert task["finished_at"] is not None


def test_list_scan_tasks_empty(client):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    response = client.get(f"/scans/{scan['id']}/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_scan_tasks_unknown_scan_404(client):
    response = client.get(f"/scans/{uuid.uuid4()}/tasks")
    assert response.status_code == 404
