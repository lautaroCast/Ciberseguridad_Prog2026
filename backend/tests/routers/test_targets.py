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


def test_patch_target_updates_description(client):
    created = client.post("/targets", json={"name": "for-patch", "host": "dvwa"}).json()
    response = client.patch(f"/targets/{created['id']}", json={"description": "updated"})
    assert response.status_code == 200
    assert response.json()["description"] == "updated"


def test_patch_target_can_clear_description_to_null(client):
    created = client.post(
        "/targets", json={"name": "for-patch-clear", "host": "dvwa", "description": "initial"}
    ).json()
    response = client.patch(f"/targets/{created['id']}", json={"description": None})
    assert response.status_code == 200
    assert response.json()["description"] is None


def test_patch_target_deactivate_and_reactivate(client):
    created = client.post("/targets", json={"name": "for-toggle", "host": "dvwa"}).json()
    assert created["is_active"] is True

    deactivated = client.patch(f"/targets/{created['id']}", json={"is_active": False})
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    reactivated = client.patch(f"/targets/{created['id']}", json={"is_active": True})
    assert reactivated.status_code == 200
    assert reactivated.json()["is_active"] is True


def test_patch_target_rejects_null_is_active(client):
    # Regression (docs/independent-evaluation-report.md, Recomendación #6):
    # is_active is NOT NULL DB-side — a null here used to reach an
    # unhandled IntegrityError (500) instead of a clean 422.
    created = client.post("/targets", json={"name": "for-null-active", "host": "dvwa"}).json()
    response = client.patch(f"/targets/{created['id']}", json={"is_active": None})
    assert response.status_code == 422


def test_patch_target_omitting_is_active_leaves_it_unchanged(client):
    created = client.post("/targets", json={"name": "for-omit", "host": "dvwa"}).json()
    client.patch(f"/targets/{created['id']}", json={"is_active": False})

    response = client.patch(f"/targets/{created['id']}", json={"description": "only this changes"})
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["description"] == "only this changes"


def test_patch_target_not_found(client):
    import uuid

    response = client.patch(f"/targets/{uuid.uuid4()}", json={"description": "x"})
    assert response.status_code == 404


def test_delete_target_happy_path(client):
    created = client.post("/targets", json={"name": "for-delete", "host": "dvwa"}).json()
    response = client.delete(f"/targets/{created['id']}")
    assert response.status_code == 204

    follow_up = client.get(f"/targets/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_target_not_found(client):
    import uuid

    response = client.delete(f"/targets/{uuid.uuid4()}")
    assert response.status_code == 404
