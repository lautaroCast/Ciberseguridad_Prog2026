from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


def _client_with_output_dir(tmp_path: Path) -> TestClient:
    app.dependency_overrides[get_settings] = lambda: Settings(
        reports_output_dir=str(tmp_path)
    )
    client = TestClient(app)
    return client


def test_create_report_writes_file(sample_report_request, tmp_path: Path):
    client = _client_with_output_dir(tmp_path)
    try:
        request = sample_report_request.model_copy(update={"format": "json"})
        response = client.post("/reports", json=request.model_dump(mode="json"))
        assert response.status_code == 200
        body = response.json()
        assert body["filename"] == f"{request.scan.id}.json"
        assert (tmp_path / body["filename"]).exists()
    finally:
        app.dependency_overrides.clear()


def test_download_report_happy_path(sample_report_request, tmp_path: Path):
    client = _client_with_output_dir(tmp_path)
    try:
        request = sample_report_request.model_copy(update={"format": "json"})
        create_response = client.post("/reports", json=request.model_dump(mode="json"))
        filename = create_response.json()["filename"]

        response = client.get(f"/reports/{filename}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
    finally:
        app.dependency_overrides.clear()


def test_download_report_path_traversal_rejected(tmp_path: Path):
    client = _client_with_output_dir(tmp_path)
    try:
        # Create a real file outside the reports output dir to prove
        # traversal can't reach it. Percent-encode the slash so the value
        # reaches the `filename` path param as a single segment containing
        # "../secret.txt" (an un-encoded "/" would instead 404 at Starlette's
        # own router before ever reaching our handler — a different, less
        # meaningful assertion than confirming the app's own guard rejects it).
        secret = tmp_path.parent / "secret.txt"
        secret.write_text("should not be reachable")

        response = client.get("/reports/..%2Fsecret.txt")
        assert response.status_code == 404
        assert "should not be reachable" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_download_report_unknown_filename(tmp_path: Path):
    client = _client_with_output_dir(tmp_path)
    try:
        response = client.get("/reports/does-not-exist.json")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
