"""Ronda L: report_service.generate_report had no direct unit coverage —
this covers the retried-Generate-Report idempotency fix (ix_reports_
scan_id_format's unique index + IntegrityError catch)."""

import httpx
import pytest

from app.services import report_service, scan_service, target_service


def _make_scan(db_session):
    target = target_service.register_target(
        db_session, name="juice-shop-demo", host="juice-shop", description=None
    )
    return scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)


class _FakeResponse:
    def __init__(self, json_body):
        self._json_body = json_body

    def json(self):
        return self._json_body

    def raise_for_status(self):
        pass


def test_generate_report_retried_after_first_success_returns_existing_row(db_session, monkeypatch):
    """n8n's Generate Report node retries on transient failures - a lost/
    delayed response to a call that already rendered and persisted the
    report must not duplicate the Report row on the retry."""
    scan = _make_scan(db_session)

    def _fake_post(url, json, headers, timeout):
        return _FakeResponse({"format": "pdf", "filename": f"{scan.id}.pdf"})

    monkeypatch.setattr(httpx, "post", _fake_post)

    first = report_service.generate_report(db_session, scan.id, "pdf")
    retried = report_service.generate_report(db_session, scan.id, "pdf")

    assert retried.id == first.id
    reports = report_service.list_reports_for_scan(db_session, scan.id)
    assert len(reports) == 1


def test_generate_report_different_formats_are_not_deduplicated(db_session, monkeypatch):
    scan = _make_scan(db_session)

    def _fake_post(url, json, headers, timeout):
        fmt = json["format"]
        return _FakeResponse({"format": fmt, "filename": f"{scan.id}.{fmt}"})

    monkeypatch.setattr(httpx, "post", _fake_post)

    pdf = report_service.generate_report(db_session, scan.id, "pdf")
    html = report_service.generate_report(db_session, scan.id, "html")

    assert pdf.id != html.id
    reports = report_service.list_reports_for_scan(db_session, scan.id)
    assert len(reports) == 2


def test_generate_report_integrity_error_not_explained_by_a_duplicate_reraises(
    db_session, monkeypatch
):
    """Same defensive re-raise as scan_task_service's identical catch:
    an IntegrityError the unique index doesn't actually explain (e.g. a
    genuine FK violation) must propagate, not be silently swallowed."""
    from sqlalchemy.exc import IntegrityError

    scan = _make_scan(db_session)

    def _fake_post(url, json, headers, timeout):
        return _FakeResponse({"format": "pdf", "filename": f"{scan.id}.pdf"})

    monkeypatch.setattr(httpx, "post", _fake_post)

    from app.repositories import report_repository

    def _raise_integrity_error(*args, **kwargs):
        raise IntegrityError("boom", params=None, orig=Exception("boom"))

    monkeypatch.setattr(report_repository, "create_report", _raise_integrity_error)
    monkeypatch.setattr(
        report_repository, "get_report_by_scan_and_format", lambda *a, **k: None
    )

    with pytest.raises(IntegrityError):
        report_service.generate_report(db_session, scan.id, "pdf")
