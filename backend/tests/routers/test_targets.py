def test_create_target_happy_path(client):
    response = client.post(
        "/targets", json={"name": "juice-shop-demo", "host": "juice-shop", "description": "demo"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "juice-shop-demo"
    assert body["host"] == "juice-shop"
    assert body["is_lab_target"] is True


def test_create_target_disallowed_host(client):
    response = client.post("/targets", json={"name": "evil", "host": "evil.example.com"})
    assert response.status_code == 422
    assert "whitelist" in response.json()["detail"]


def test_create_target_duplicate_name(client):
    payload = {"name": "dup-target", "host": "juice-shop"}
    first = client.post("/targets", json=payload)
    assert first.status_code == 201

    second = client.post("/targets", json={"name": "dup-target", "host": "dvwa"})
    assert second.status_code == 409


def test_get_target_malformed_uuid(client):
    response = client.get("/targets/not-a-uuid")
    assert response.status_code == 422


def test_get_target_not_found(client):
    import uuid

    response = client.get(f"/targets/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_target_happy_path(client):
    created = client.post("/targets", json={"name": "for-get", "host": "dvwa"}).json()
    response = client.get(f"/targets/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "for-get"
