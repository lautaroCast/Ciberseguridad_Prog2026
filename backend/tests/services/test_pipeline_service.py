"""COD-6: pipeline_service.trigger_pipeline had zero test coverage — this
is "the only place the Backend talks to n8n" per its own docstring, and it
has a failure branch (mark the just-created Scan FAILED on httpx.HTTPError)
that was completely unverified. No prior test in this repo mocks httpx, so
this establishes the pattern via monkeypatch.setattr(httpx, "post", ...)."""

import os

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

    def _fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
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
    assert captured["headers"] == {"X-Webhook-Secret": os.environ["N8N_WEBHOOK_SECRET"]}


def test_trigger_pipeline_failure_marks_scan_failed(db_session, monkeypatch):
    target = _make_target(db_session)

    def _fake_post(url, json, headers, timeout):
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


def test_trigger_pipeline_while_one_is_already_running_raises(db_session, monkeypatch):
    # 8th independent evaluation: two concurrent "Correr pipeline" triggers
    # against the same target used to be able to create two scans at once -
    # against dvwa this is consequential since dvwa_auth.
    # get_authenticated_cookie mutates shared server-side session state a
    # second concurrent scan would also mutate mid-run.
    target = _make_target(db_session)
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResponse(200))

    pipeline_service.trigger_pipeline(db_session, target.id)

    with pytest.raises(scan_service.ScanAlreadyRunningError):
        pipeline_service.trigger_pipeline(db_session, target.id)

    scans = scan_service.list_scans_for_target(db_session, target.id)
    assert len(scans) == 1
