"""X-API-Key enforcement on user-facing routers.

Uses the `client` fixture's default headers (see conftest.py) as the
"correct key" baseline, then overrides X-API-Key per-request to exercise
the missing/wrong-key paths — TestClient merges per-call headers on top of
the client's defaults.
"""


def test_targets_without_api_key_is_rejected(client):
    client.headers.pop("X-API-Key")
    response = client.get("/targets")
    assert response.status_code == 401


def test_targets_with_wrong_api_key_is_rejected(client):
    response = client.get("/targets", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


def test_targets_with_correct_api_key_succeeds(client):
    response = client.get("/targets")
    assert response.status_code == 200


def test_health_requires_no_api_key(client):
    client.headers.pop("X-API-Key")
    response = client.get("/health")
    assert response.status_code == 200
