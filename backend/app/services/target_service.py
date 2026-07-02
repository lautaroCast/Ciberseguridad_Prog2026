"""Business rules for targets — the whitelist enforcement lives here.

This is the single place that decides whether a host may ever be
registered as a scan target. Every other layer (routers, repository,
eventually the Scanner Service via the API) trusts that a `Target` row
existing in the database means it was already validated here.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.repositories import target_repository
from models import Target


class TargetNotAllowedError(Exception):
    """Raised when a host is not part of the local lab whitelist."""


class TargetNameConflictError(Exception):
    """Raised when a target name is already registered."""


class TargetNotFoundError(Exception):
    """Raised when a target id does not exist."""


def list_targets(db: Session, *, is_active: bool | None = None) -> list[Target]:
    return target_repository.list_targets(db, is_active=is_active)


def get_target_or_raise(db: Session, target_id: uuid.UUID) -> Target:
    target = target_repository.get_target(db, target_id)
    if target is None:
        raise TargetNotFoundError(str(target_id))
    return target


def register_target(db: Session, *, name: str, host: str, description: str | None) -> Target:
    settings = get_settings()
    if host not in settings.allowed_lab_hosts:
        raise TargetNotAllowedError(host)

    if target_repository.get_target_by_name(db, name) is not None:
        raise TargetNameConflictError(name)

    # The check above is an optimistic fast path, not the source of truth:
    # it's not atomic with the insert below, so two concurrent requests for
    # the same name can both pass it. `targets.name` has a DB-level unique
    # constraint (database/models/target.py) that is the real guard —
    # catching its violation here turns a would-be unhandled 500 into the
    # same 409 the pre-check produces on the non-racy path.
    try:
        return target_repository.create_target(db, name=name, host=host, description=description)
    except IntegrityError as exc:
        db.rollback()
        raise TargetNameConflictError(name) from exc


def update_target(db: Session, target_id: uuid.UUID, updates: dict) -> Target:
    target = get_target_or_raise(db, target_id)
    return target_repository.update_target(db, target, updates)


def delete_target(db: Session, target_id: uuid.UUID) -> None:
    target = get_target_or_raise(db, target_id)
    target_repository.delete_target(db, target)
