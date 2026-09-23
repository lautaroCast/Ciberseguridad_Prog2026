import uuid

import pytest
from models import ScanStatus

from app.services import scan_service, target_service


def _make_target(db_session, name="juice-shop-demo", host="juice-shop"):
    return target_service.register_target(db_session, name=name, host=host, description=None)


def test_list_scans_for_target_ordered_newest_first(db_session):
    # created_at is a DB-side CURRENT_TIMESTAMP default with only 1-second
    # resolution under SQLite, so two scans created back-to-back in the same
    # test can tie — set the timestamps explicitly here rather than relying
    # on real wall-clock separation between the two create_scan() calls.
    target = _make_target(db_session)
    first = scan_service.create_scan(db_session, target_id=target.id, triggered_by="a")
    # ix_scans_one_active_per_host only allows one non-terminal scan per
    # host - complete the first before creating the second, same as a
    # real sequential history would look.
    scan_service.complete_scan(db_session, first.id, status=ScanStatus.COMPLETED, error_message=None)
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


def test_complete_scan_twice_with_same_status_is_idempotent(db_session):
    """Ronda L: Complete Scan's own retryOnFail (n8n) can re-send the same
    completion after its first response was lost/timed out — the first
    attempt already committed, so this must return the existing scan, not
    a false 409 that would stall the pipeline before Generate Report."""
    target = _make_target(db_session)
    scan = scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)
    first = scan_service.complete_scan(
        db_session, scan.id, status=ScanStatus.COMPLETED, error_message=None
    )

    retried = scan_service.complete_scan(
        db_session, scan.id, status=ScanStatus.COMPLETED, error_message=None
    )

    assert retried.id == first.id
    assert retried.status == ScanStatus.COMPLETED
    assert retried.finished_at == first.finished_at


@pytest.mark.postgres
def test_complete_scan_loses_race_returns_existing_scan(postgres_session_pair, monkeypatch):
    """Ronda M: scan_service.py:136-143 (the conditional UPDATE losing the
    race between this function's own pre-check and its write) had no
    test - only the pre-check's idempotent-retry path was covered above
    (test_complete_scan_twice_with_same_status_is_idempotent). This forces
    the actual race window: session B's pre-check reads RUNNING, then
    session A's full completion commits before session B's own UPDATE
    runs, so B's conditional UPDATE affects 0 rows and must fall back to
    re-fetching and applying the same idempotent-retry rule - proving the
    fallback branch itself works, not just the pre-check."""
    import threading

    from app.repositories import scan_repository

    session_a, session_b = postgres_session_pair
    target = _make_target(session_a)
    scan = scan_service.create_scan(session_a, target_id=target.id, triggered_by=None)
    scan_id = scan.id
    session_a.commit()  # make the scan visible to session_b

    precheck_done = threading.Event()
    proceed = threading.Event()
    real_repo_complete_scan = scan_repository.complete_scan

    def _delayed_repo_complete_scan(db, *args, **kwargs):
        if db is session_b:
            precheck_done.set()
            assert proceed.wait(timeout=5), "session A never signalled it had committed"
        return real_repo_complete_scan(db, *args, **kwargs)

    monkeypatch.setattr(scan_repository, "complete_scan", _delayed_repo_complete_scan)

    result: dict = {}

    def _try_complete_b():
        result["scan"] = scan_service.complete_scan(
            session_b, scan_id, status=ScanStatus.COMPLETED, error_message=None
        )

    thread = threading.Thread(target=_try_complete_b)
    thread.start()
    assert precheck_done.wait(timeout=5), "session B should have reached its own UPDATE call"

    # Session A completes for real while B is paused right before its own
    # UPDATE - B's pre-check already read RUNNING, so it must lose the race.
    scan_service.complete_scan(session_a, scan_id, status=ScanStatus.COMPLETED, error_message=None)
    session_a.commit()

    proceed.set()
    thread.join(timeout=5)
    assert not thread.is_alive(), "session B should have returned once unblocked, not hung"
    assert result["scan"].status == ScanStatus.COMPLETED


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


def test_create_scan_while_one_is_already_running_raises(db_session):
    # 8th independent evaluation: create_scan only checked
    # Target.is_active, never whether the target already had a
    # non-terminal scan - ix_scans_one_active_per_host is the real
    # guard (a partial unique index), this proves the service surfaces it
    # as a clean domain exception rather than a raw IntegrityError.
    target = _make_target(db_session)
    first = scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)

    with pytest.raises(scan_service.ScanAlreadyRunningError):
        scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)

    # The first scan must be completely unaffected by the failed second
    # attempt (no partial write, no rollback side effect on it).
    reloaded = scan_service.get_scan_or_raise(db_session, first.id)
    assert reloaded.status == ScanStatus.RUNNING


def test_create_scan_target_deleted_mid_flight_raises_target_not_found(db_session, monkeypatch):
    # Same IntegrityError symptom as
    # test_create_scan_while_one_is_already_running_raises above
    # (ix_scans_one_active_per_host), but this time from scans.target_id's
    # FK — simulated by deleting the target row inside create_scan, in the
    # window between get_active_target_or_raise's check and the insert.
    from sqlalchemy.exc import IntegrityError

    from app.repositories import target_repository

    target = _make_target(db_session)

    def _fake_create_scan(db, *, target_id, host, triggered_by):
        target_repository.delete_target(db, target_id)
        raise IntegrityError("insert into scans", {}, Exception("fk violation"))

    monkeypatch.setattr(scan_service.scan_repository, "create_scan", _fake_create_scan)

    with pytest.raises(target_service.TargetNotFoundError):
        scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)


def test_create_scan_while_a_sibling_target_on_the_same_host_is_running_raises(db_session):
    # 2026-09-06 correction round: two different Target rows can point at
    # the same physical host (nothing prevents that, by design - see the
    # docs/installation.md pagination test and register_target's own
    # lack of a host uniqueness check). Before this fix,
    # ix_scans_one_active_per_target was keyed on target_id, so a scan
    # against target_b here would never have collided with the one
    # already running against target_a, even though they share a host -
    # exactly the race scanner/app/services/dvwa_auth.py's shared
    # session-state mutation is vulnerable to. host is now denormalized
    # onto Scan and the index is keyed on it instead, so this must raise.
    target_a = _make_target(db_session, name="dvwa-a", host="dvwa")
    target_b = _make_target(db_session, name="dvwa-b", host="dvwa")
    scan_service.create_scan(db_session, target_id=target_a.id, triggered_by=None)

    with pytest.raises(scan_service.ScanAlreadyRunningError):
        scan_service.create_scan(db_session, target_id=target_b.id, triggered_by=None)


def test_create_scan_allowed_again_once_the_first_reaches_a_terminal_status(db_session):
    target = _make_target(db_session)
    first = scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)
    scan_service.complete_scan(db_session, first.id, status=ScanStatus.FAILED, error_message="x")

    second = scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)

    assert second.id != first.id
    assert second.status == ScanStatus.RUNNING


def test_list_scans_for_target_does_not_leak_other_targets_scans(db_session):
    # host must differ between the two targets: Target.host itself has no
    # uniqueness constraint (two targets *can* share a host, see
    # test_create_scan_while_a_sibling_target_on_the_same_host_is_running_raises
    # above) - but if both targets here shared a host, creating a
    # non-terminal scan for each would collide against
    # ix_scans_one_active_per_host (database/models/scan.py), which is
    # not what this test is exercising (target-scoped listing isolation).
    target_a = _make_target(db_session, name="target-a", host="juice-shop")
    target_b = _make_target(db_session, name="target-b", host="dvwa")
    scan_service.create_scan(db_session, target_id=target_a.id, triggered_by=None)
    scan_b = scan_service.create_scan(db_session, target_id=target_b.id, triggered_by=None)

    scans = scan_service.list_scans_for_target(db_session, target_b.id)

    assert [s.id for s in scans] == [scan_b.id]
