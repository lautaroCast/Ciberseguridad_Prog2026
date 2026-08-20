"""COD-6: pipeline_service.trigger_pipeline had zero test coverage — this
is "the only place the Backend talks to n8n" per its own docstring, and it
has a failure branch (mark the just-created Scan FAILED on httpx.HTTPError)
that was completely unverified. No prior test in this repo mocks httpx, so
this establishes the pattern via monkeypatch.setattr(httpx, "post", ...)."""

import httpx
import pytest

from app.services import pipeline_service, scan_service, target_service
from models import ScanStatus


def _make_target(db_session):
    return target_service.register_target(
        db_session, name="juice-shop-demo", host="juice-shop", description=None
    )


class _FakeResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=None, response=self)


def test_trigger_pipeline_success_sends_expected_payload(db_session, monkeypatch):
    target = _make_target(db_session)
    captured = {}

    def _fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResponse(200)

    monkeypatch.setattr(httpx, "post", _fake_post)

    scan = pipeline_service.trigger_pipeline(db_session, target.id)

    assert scan.id is not None
    assert scan.target_id == target.id
    assert captured["url"] == "http://n8n:5678/webhook/vulnscan-pipeline"
    assert captured["json"] == {
        "scan_id": str(scan.id),
        "target_id": str(target.id),
        "host": "juice-shop",
    }


def test_trigger_pipeline_failure_marks_scan_failed(db_session, monkeypatch):
    target = _make_target(db_session)

    def _fake_post(url, json, timeout):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", _fake_post)

    with pytest.raises(pipeline_service.PipelineTriggerError):
        pipeline_service.trigger_pipeline(db_session, target.id)

    # the Scan row was created before the webhook call — it must not be
    # left "running" forever just because the trigger itself failed.
    scans = scan_service.list_scans_for_target(db_session, target.id)
    assert len(scans) == 1
    assert scans[0].status == ScanStatus.FAILED
    assert "connection refused" in scans[0].error_message


def test_trigger_pipeline_unknown_target_raises(db_session):
    import uuid

    with pytest.raises(target_service.TargetNotFoundError):
        pipeline_service.trigger_pipeline(db_session, uuid.uuid4())


def test_trigger_pipeline_on_inactive_target_raises(db_session):
    target = _make_target(db_session)
    target_service.update_target(db_session, target.id, {"is_active": False})

    with pytest.raises(target_service.TargetInactiveError):
        pipeline_service.trigger_pipeline(db_session, target.id)
