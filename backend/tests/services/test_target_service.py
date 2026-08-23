import uuid

import pytest

from app.repositories import target_repository
from app.services import scan_service, target_service
from models import ScanStatus


def test_register_target_with_allowed_host(db_session):
    target = target_service.register_target(
        db_session, name="juice-shop-demo", host="juice-shop", description="demo"
    )
    assert target.id is not None
    assert target.name == "juice-shop-demo"
    assert target.host == "juice-shop"
    assert target.is_lab_target is True


def test_register_target_with_disallowed_host_raises(db_session):
    with pytest.raises(target_service.TargetNotAllowedError):
        target_service.register_target(
            db_session, name="evil", host="evil.example.com", description=None
        )


def test_register_target_duplicate_name_via_service_precheck(db_session):
    target_service.register_target(db_session, name="dup", host="juice-shop", description=None)
    with pytest.raises(target_service.TargetNameConflictError):
        target_service.register_target(db_session, name="dup", host="dvwa", description=None)


def test_register_target_duplicate_name_via_integrity_error(db_session, monkeypatch):
    # register_target()'s pre-check (get_target_by_name) always short-circuits
    # a same-process duplicate call before reaching the try/except around
    # create_target() — that except only exists for a genuine race between
    # two concurrent requests, where both pass the pre-check before either
    # commits. Simulate that race by monkeypatching the pre-check to always
    # report "no existing row", forcing the second insert to rely on the DB's
    # own unique constraint (and the service's IntegrityError -> domain-error
    # translation) instead of the optimistic check.
    target_repository.create_target(db_session, name="raced", host="juice-shop", description=None)
    monkeypatch.setattr(target_repository, "get_target_by_name", lambda db, name: None)
    with pytest.raises(target_service.TargetNameConflictError):
        target_service.register_target(db_session, name="raced", host="dvwa", description=None)


def test_get_target_or_raise_not_found(db_session):
    with pytest.raises(target_service.TargetNotFoundError):
        target_service.get_target_or_raise(db_session, uuid.uuid4())


def test_delete_target_rejects_when_a_scan_is_still_running(db_session):
    target = target_service.register_target(
        db_session, name="active-scan-target", host="juice-shop", description=None
    )
    scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)

    with pytest.raises(target_service.TargetHasActiveScansError):
        target_service.delete_target(db_session, target.id)

    # The target must survive the rejected deletion attempt.
    assert target_repository.get_target(db_session, target.id) is not None


def test_delete_target_succeeds_when_all_scans_are_terminal(db_session):
    target = target_service.register_target(
        db_session, name="finished-scan-target", host="juice-shop", description=None
    )
    scan = scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)
    scan_service.complete_scan(db_session, scan.id, status=ScanStatus.COMPLETED, error_message=None)

    target_service.delete_target(db_session, target.id)

    assert target_repository.get_target(db_session, target.id) is None


def test_delete_target_succeeds_with_no_scans_at_all(db_session):
    target = target_service.register_target(
        db_session, name="never-scanned-target", host="juice-shop", description=None
    )

    target_service.delete_target(db_session, target.id)

    assert target_repository.get_target(db_session, target.id) is None
