import uuid


def _create_target(client):
    response = client.post("/targets", json={"name": "juice-shop-demo", "host": "juice-shop"})
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
