"""COD-6: backend/app/routers/reports.py had zero tests — this covers
create_report/list_reports/download_report happy paths, the 404/upstream-
error passthrough, and the COD-11 file_path sanitization regression."""

import uuid

import httpx

from app.services import report_service


def _create_target(client):
    return client.post("/targets", json={"name": "juice-shop-demo", "host": "juice-shop"}).json()


def _create_scan(client, target_id):
    return client.post(f"/targets/{target_id}/scans", json={}).json()


class _FakeResponse:
    def __init__(self, status_code=200, json_body=None, content=b""):
        self.status_code = status_code
        self._json_body = json_body
        self.content = content

    def json(self):
        return self._json_body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=None, response=self)


def test_create_report_happy_path(client, monkeypatch):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    def _fake_post(url, json, headers, timeout):
        return _FakeResponse(200, json_body={"format": "pdf", "filename": f"{scan['id']}.pdf"})

    monkeypatch.setattr(httpx, "post", _fake_post)

    response = client.post(f"/scans/{scan['id']}/reports", params={"format": "pdf"})
    assert response.status_code == 201
    body = response.json()
    assert body["format"] == "pdf"
    assert body["file_path"] == f"{scan['id']}.pdf"


def test_create_report_rejects_unsafe_filename_from_upstream(client, monkeypatch):
    # Regression: the safety check used to be enforced only at
    # download-time; a malformed/malicious filename in the Reports
    # Service's own response was persisted verbatim. Now checked at
    # write time too, in report_service.generate_report.
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    def _fake_post(url, json, headers, timeout):
        return _FakeResponse(200, json_body={"format": "pdf", "filename": "../../etc/passwd"})

    monkeypatch.setattr(httpx, "post", _fake_post)

    response = client.post(f"/scans/{scan['id']}/reports", params={"format": "pdf"})
    assert response.status_code == 500


def test_create_report_rejects_bare_dotdot_filename_from_upstream(client, monkeypatch):
    # Regression: every character in ".." is individually allowed by
    # _SAFE_FILENAME, and no "/" is needed to reach a parent directory —
    # fullmatch let a bare ".."/"." through even though it's exactly what
    # this check exists to reject.
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    def _fake_post(url, json, headers, timeout):
        return _FakeResponse(200, json_body={"format": "pdf", "filename": ".."})

    monkeypatch.setattr(httpx, "post", _fake_post)

    response = client.post(f"/scans/{scan['id']}/reports", params={"format": "pdf"})
    assert response.status_code == 500


def test_download_report_rejects_trailing_newline_in_file_path(client, db_session):
    # Regression: the old `^...$` regex (via `.match`) lets a value ending
    # in "\n" through, since `$` matches just before one trailing newline.
    # `fullmatch` on a pattern with no `\n` in its character class doesn't
    # have that leniency.
    target = _create_target(client)
    scan = _create_scan(client, target["id"])
    report = report_service.report_repository.create_report(
        db_session,
        scan_id=uuid.UUID(scan["id"]),
        format=report_service.ReportFormat("json"),
        file_path="abc123.json\n",
        generated_by="test",
    )
    db_session.commit()

    response = client.get(f"/reports/{report.id}/download")
    assert response.status_code == 500


def test_create_report_upstream_error_returns_502(client, monkeypatch):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    def _fake_post(url, json, headers, timeout):
        raise httpx.ConnectError("reports service unreachable")

    monkeypatch.setattr(httpx, "post", _fake_post)

    response = client.post(f"/scans/{scan['id']}/reports", params={"format": "pdf"})
    assert response.status_code == 502


def test_create_report_malformed_json_returns_502(client, monkeypatch):
    # A 200 response isn't a guarantee of a well-formed body — e.g. a proxy
    # in front of the Reports Service returning its own HTML error page
    # with a 200. response.json() raising ValueError used to fall through
    # as an unhandled 500 instead of the same 502 path as an unreachable
    # upstream.
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    class _BrokenJsonResponse(_FakeResponse):
        def json(self):
            raise ValueError("not valid JSON")

    def _fake_post(url, json, headers, timeout):
        return _BrokenJsonResponse(200)

    monkeypatch.setattr(httpx, "post", _fake_post)

    response = client.post(f"/scans/{scan['id']}/reports", params={"format": "pdf"})
    assert response.status_code == 502


def test_create_report_missing_key_returns_502(client, monkeypatch):
    # Valid JSON, but missing the "filename" key generate_report expects —
    # same fix as the malformed-JSON case above, same regression class.
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    def _fake_post(url, json, headers, timeout):
        return _FakeResponse(200, json_body={"format": "pdf"})

    monkeypatch.setattr(httpx, "post", _fake_post)

    response = client.post(f"/scans/{scan['id']}/reports", params={"format": "pdf"})
    assert response.status_code == 502


def test_list_reports_for_scan(client, monkeypatch):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])
    monkeypatch.setattr(
        httpx,
        "post",
        lambda url, json, headers, timeout: _FakeResponse(
            200, json_body={"format": "json", "filename": f"{scan['id']}.json"}
        ),
    )
    client.post(f"/scans/{scan['id']}/reports", params={"format": "json"})

    response = client.get(f"/scans/{scan['id']}/reports")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_download_report_happy_path(client, monkeypatch):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])
    monkeypatch.setattr(
        httpx,
        "post",
        lambda url, json, headers, timeout: _FakeResponse(
            200, json_body={"format": "json", "filename": f"{scan['id']}.json"}
        ),
    )
    created = client.post(f"/scans/{scan['id']}/reports", params={"format": "json"}).json()

    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, headers, timeout: _FakeResponse(200, content=b'{"ok": true}'),
    )
    response = client.get(f"/reports/{created['id']}/download")
    assert response.status_code == 200
    assert response.content == b'{"ok": true}'
    assert created["file_path"] in response.headers["content-disposition"]


def test_download_report_unavailable_returns_502(client, monkeypatch):
    target = _create_target(client)
    scan = _create_scan(client, target["id"])
    monkeypatch.setattr(
        httpx,
        "post",
        lambda url, json, headers, timeout: _FakeResponse(
            200, json_body={"format": "json", "filename": f"{scan['id']}.json"}
        ),
    )
    created = client.post(f"/scans/{scan['id']}/reports", params={"format": "json"}).json()

    monkeypatch.setattr(httpx, "get", lambda url, headers, timeout: _FakeResponse(404))
    response = client.get(f"/reports/{created['id']}/download")
    assert response.status_code == 502


def test_download_report_unknown_id_404s(client):
    response = client.get(f"/reports/{uuid.uuid4()}/download")
    assert response.status_code == 404


def test_download_report_rejects_unsafe_stored_file_path(client, db_session, monkeypatch):
    # COD-11 regression: file_path is meant to always be "{uuid}.{ext}",
    # generated by the Reports Service — but it's still an external
    # response value stored verbatim. If it were ever something else
    # (e.g. containing "/" or a quote), the router must reject it before
    # building a URL or a Content-Disposition header from it, not
    # interpolate it blindly.
    target = _create_target(client)
    scan = _create_scan(client, target["id"])

    report = report_service.report_repository.create_report(
        db_session,
        scan_id=uuid.UUID(scan["id"]),
        format=report_service.ReportFormat("json"),
        file_path='evil"; ../../etc/passwd',
        generated_by="test",
    )
    db_session.commit()

    response = client.get(f"/reports/{report.id}/download")
    assert response.status_code == 500
