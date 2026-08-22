import uuid

import pytest

from app.services import scan_service, target_service
from models import ScanStatus


def _make_target(db_session, name="juice-shop-demo"):
    return target_service.register_target(db_session, name=name, host="juice-shop", description=None)


def test_list_scans_for_target_ordered_newest_first(db_session):
    # created_at is a DB-side CURRENT_TIMESTAMP default with only 1-second
    # resolution under SQLite, so two scans created back-to-back in the same
    # test can tie — set the timestamps explicitly here rather than relying
    # on real wall-clock separation between the two create_scan() calls.
    target = _make_target(db_session)
    first = scan_service.create_scan(db_session, target_id=target.id, triggered_by="a")
    second = scan_service.create_scan(db_session, target_id=target.id, triggered_by="b")

    from datetime import UTC, datetime

    first.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    second.created_at = datetime(2026, 1, 2, tzinfo=UTC)
    db_session.commit()

    scans = scan_service.list_scans_for_target(db_session, target.id)

    assert [s.id for s in scans] == [second.id, first.id]


def test_list_scans_for_target_empty(db_session):
    target = _make_target(db_session)
    assert scan_service.list_scans_for_target(db_session, target.id) == []


def test_list_scans_for_target_unknown_target_raises(db_session):
    with pytest.raises(target_service.TargetNotFoundError):
        scan_service.list_scans_for_target(db_session, uuid.uuid4())


def test_create_scan_on_inactive_target_raises(db_session):
    target = _make_target(db_session)
    target_service.update_target(db_session, target.id, {"is_active": False})

    with pytest.raises(target_service.TargetInactiveError):
        scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)


def test_complete_scan_twice_raises(db_session):
    target = _make_target(db_session)
    scan = scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)
    scan_service.complete_scan(db_session, scan.id, status=ScanStatus.COMPLETED, error_message=None)

    with pytest.raises(scan_service.ScanAlreadyTerminalError):
        scan_service.complete_scan(db_session, scan.id, status=ScanStatus.FAILED, error_message="x")


def test_complete_scan_persists_pipeline_run_id(db_session):
    # n8n sends its own $execution.id on the Complete Scan / Mark Scan
    # Failed nodes so this column (docs/database.md) actually correlates
    # a scan with the n8n execution that produced it, instead of staying
    # unpopulated.
    target = _make_target(db_session)
    scan = scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)

    updated = scan_service.complete_scan(
        db_session,
        scan.id,
        status=ScanStatus.COMPLETED,
        error_message=None,
        pipeline_run_id="12345",
    )

    assert updated.pipeline_run_id == "12345"


def test_complete_scan_without_pipeline_run_id_leaves_it_unset(db_session):
    target = _make_target(db_session)
    scan = scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)

    updated = scan_service.complete_scan(
        db_session, scan.id, status=ScanStatus.COMPLETED, error_message=None
    )

    assert updated.pipeline_run_id is None


def test_list_scans_for_target_does_not_leak_other_targets_scans(db_session):
    target_a = _make_target(db_session, name="target-a")
    target_b = _make_target(db_session, name="target-b")
    scan_service.create_scan(db_session, target_id=target_a.id, triggered_by=None)
    scan_b = scan_service.create_scan(db_session, target_id=target_b.id, triggered_by=None)

    scans = scan_service.list_scans_for_target(db_session, target_b.id)

    assert [s.id for s in scans] == [scan_b.id]
