"""COD-6: scan_task_service.ingest_scan_task had zero test coverage despite
being described as "Módulo 5's core" — this covers the happy path (real
counts from a real normalizer), the normalizer-failure-doesn't-fail-ingest
branch, and the service_id-always-None behavior (COD-10)."""

from datetime import UTC, datetime

import pytest

from app.services import scan_task_service, scan_service, target_service


def _make_scan(db_session):
    target = target_service.register_target(
        db_session, name="juice-shop-demo", host="juice-shop", description=None
    )
    return scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)


def _ingest(db_session, scan_id, **overrides):
    now = datetime.now(UTC)
    kwargs = dict(
        tool="nmap",
        command="nmap -sV juice-shop",
        status="completed",
        started_at=now,
        finished_at=now,
        raw_output="<nmaprun></nmaprun>",
        parsed=None,
        error_message=None,
    )
    kwargs.update(overrides)
    return scan_task_service.ingest_scan_task(db_session, scan_id, **kwargs)


def test_ingest_happy_path_creates_services_from_normalizer(db_session):
    scan = _make_scan(db_session)
    result = _ingest(
        db_session,
        scan.id,
        tool="nmap",
        parsed=[{"host": "juice-shop", "port": 80, "service_name": "http"}],
    )
    assert result.services_upserted == 1
    assert result.technologies_created == 0
    assert result.findings_created == 0
    assert result.scan_task.tool_name == "nmap"


def test_ingest_happy_path_creates_findings_from_normalizer(db_session):
    scan = _make_scan(db_session)
    result = _ingest(
        db_session,
        scan.id,
        tool="nuclei",
        parsed=[
            {
                "template-id": "exposed-panel",
                "type": "http",
                "host": "juice-shop",
                "matched-at": "http://juice-shop/admin",
                "info": {"name": "Exposed Admin Panel", "severity": "high"},
            }
        ],
    )
    assert result.findings_created == 1
    # COD-10: service_id is documented as unpopulated, never a real FK match.
    task = result.scan_task
    assert task.raw_output == "<nmaprun></nmaprun>"


def test_ingest_without_parsed_creates_no_normalized_rows(db_session):
    scan = _make_scan(db_session)
    result = _ingest(db_session, scan.id, tool="nmap", parsed=None)
    assert result.services_upserted == 0
    assert result.findings_created == 0
    assert result.technologies_created == 0


def test_ingest_failed_status_skips_normalization_even_with_parsed(db_session):
    scan = _make_scan(db_session)
    result = _ingest(
        db_session,
        scan.id,
        tool="nmap",
        status="failed",
        parsed=[{"host": "juice-shop", "port": 80}],
        error_message="tool crashed",
    )
    assert result.services_upserted == 0
    assert result.scan_task.error_message == "tool crashed"


def test_normalizer_failure_is_recorded_not_raised(db_session, monkeypatch):
    from app.normalization import registry

    def _broken_normalizer(parsed):
        raise ValueError("malformed tool output")

    monkeypatch.setitem(registry._NORMALIZERS, "nmap", _broken_normalizer)

    scan = _make_scan(db_session)
    result = _ingest(db_session, scan.id, tool="nmap", parsed=[{"host": "x", "port": 1}])

    assert result.services_upserted == 0
    assert result.findings_created == 0
    assert "Normalization failed" in result.scan_task.error_message
    assert "malformed tool output" in result.scan_task.error_message


def test_ingest_unknown_scan_raises(db_session):
    import uuid

    with pytest.raises(scan_service.ScanNotFoundError):
        _ingest(db_session, uuid.uuid4(), tool="nmap")
