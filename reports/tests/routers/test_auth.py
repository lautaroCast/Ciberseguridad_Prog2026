"""X-Internal-Token enforcement on the /reports router."""


def test_create_report_without_internal_token_is_rejected(client, sample_report_request):
    client.headers.pop("X-Internal-Token")
    response = client.post("/reports", json=sample_report_request.model_dump(mode="json"))
    assert response.status_code == 401


def test_create_report_with_wrong_internal_token_is_rejected(client, sample_report_request):
    response = client.post(
        "/reports",
        json=sample_report_request.model_dump(mode="json"),
        headers={"X-Internal-Token": "wrong"},
    )
    assert response.status_code == 401


def test_health_requires_no_internal_token(client):
    client.headers.pop("X-Internal-Token")
    response = client.get("/health")
    assert response.status_code == 200
