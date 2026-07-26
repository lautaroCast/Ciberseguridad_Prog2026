"""X-Internal-Token enforcement on the /scan/{tool} router."""


def test_scan_without_internal_token_is_rejected(client):
    client.headers.pop("X-Internal-Token")
    response = client.post("/scan/nmap", json={"target": "dvwa"})
    assert response.status_code == 401


def test_scan_with_wrong_internal_token_is_rejected(client):
    response = client.post(
        "/scan/nmap", json={"target": "dvwa"}, headers={"X-Internal-Token": "wrong"}
    )
    assert response.status_code == 401


def test_health_requires_no_internal_token(client):
    client.headers.pop("X-Internal-Token")
    response = client.get("/health")
    assert response.status_code == 200
