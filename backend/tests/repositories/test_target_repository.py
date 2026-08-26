"""delete_target's guard against deleting a target with an active scan
used to be a Python-level check-then-act in target_service.py (list
scans, check none are non-terminal, then delete) — not atomic with the
delete itself. These tests exercise the repository directly, bypassing
target_service's own fast-path check, to prove the real guard (the
conditional DELETE's WHERE ... NOT EXISTS clause) is what actually
enforces "no active scan survives", not the Python-level pre-check
alone."""

from app.repositories import target_repository
from app.services import scan_service, target_service


def _make_target(db_session):
    return target_service.register_target(
        db_session, name="juice-shop-demo", host="juice-shop", description=None
    )


def test_delete_target_returns_false_when_a_scan_is_still_running(db_session):
    target = _make_target(db_session)
    scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)

    # Called directly, bypassing target_service.delete_target's own
    # Python-level pre-check - the conditional DELETE's own WHERE clause
    # must be what actually rejects this.
    deleted = target_repository.delete_target(db_session, target.id)

    assert deleted is False
    assert target_repository.get_target(db_session, target.id) is not None


def test_delete_target_returns_true_with_no_scans_at_all(db_session):
    target = _make_target(db_session)

    deleted = target_repository.delete_target(db_session, target.id)

    assert deleted is True
    assert target_repository.get_target(db_session, target.id) is None


def test_delete_target_returns_false_for_unknown_target_id(db_session):
    import uuid

    deleted = target_repository.delete_target(db_session, uuid.uuid4())

    assert deleted is False
