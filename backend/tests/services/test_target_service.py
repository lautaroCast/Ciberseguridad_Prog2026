import pytest

from app.repositories import target_repository
from app.services import target_service


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
    import uuid

    with pytest.raises(target_service.TargetNotFoundError):
        target_service.get_target_or_raise(db_session, uuid.uuid4())
