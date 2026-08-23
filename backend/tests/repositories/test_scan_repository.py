"""complete_scan's guard against completing an already-terminal scan used
to be a Python-level check-then-act in scan_service.py (read the status,
compare, then write) — not atomic with the write itself. These tests
exercise the repository directly, bypassing scan_service's own
fast-path check, to prove the real guard (the conditional UPDATE's WHERE
clause) is what actually enforces "only completes once", not the
Python-level pre-check alone."""

import uuid

from app.repositories import scan_repository
from app.services import scan_service, target_service
from models import ScanStatus


def _make_scan(db_session):
    target = target_service.register_target(
        db_session, name="juice-shop-demo", host="juice-shop", description=None
    )
    return scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)


def test_complete_scan_returns_none_when_already_terminal(db_session):
    scan = _make_scan(db_session)

    first = scan_repository.complete_scan(
        db_session,
        scan.id,
        status=ScanStatus.COMPLETED,
        error_message=None,
        forbidden_statuses=scan_service.TERMINAL_STATUSES,
    )
    assert first is not None
    assert first.status == ScanStatus.COMPLETED

    # Simulates a second caller that already passed its own optimistic
    # pre-check before this call landed (e.g. a retried webhook) — the
    # WHERE clause, not a prior SELECT, is what has to catch this.
    second = scan_repository.complete_scan(
        db_session,
        scan.id,
        status=ScanStatus.FAILED,
        error_message="a retried call shouldn't overwrite the first outcome",
        forbidden_statuses=scan_service.TERMINAL_STATUSES,
    )
    assert second is None

    # And the original outcome must survive untouched.
    reloaded = scan_repository.get_scan(db_session, scan.id)
    assert reloaded.status == ScanStatus.COMPLETED
    assert reloaded.error_message is None


def test_complete_scan_returns_none_for_unknown_scan_id(db_session):
    result = scan_repository.complete_scan(
        db_session,
        uuid.uuid4(),
        status=ScanStatus.COMPLETED,
        error_message=None,
        forbidden_statuses=scan_service.TERMINAL_STATUSES,
    )
    assert result is None
