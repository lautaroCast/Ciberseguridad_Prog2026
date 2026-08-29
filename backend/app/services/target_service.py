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
from app.repositories import scan_repository, target_repository
from models import TERMINAL_SCAN_STATUSES, Target


class TargetNotAllowedError(Exception):
    """Raised when a host is not part of the local lab whitelist."""


class TargetNameConflictError(Exception):
    """Raised when a target name is already registered."""


class TargetNotFoundError(Exception):
    """Raised when a target id does not exist."""


class TargetInactiveError(Exception):
    """Raised when a scan/pipeline is requested against a target that's
    been marked inactive via PATCH /targets/{id}. Read access (GET, list)
    to inactive targets is intentionally still allowed — this only gates
    the two places that would launch new work against one."""


class TargetHasActiveScansError(Exception):
    """Raised when deletion is attempted while the target has a scan that
    hasn't reached a terminal status yet. `Target.scans` cascades
    (`all, delete-orphan`) down to ScanTask/Finding, so letting this
    through would silently destroy in-flight pipeline data."""


def list_targets(
    db: Session, *, is_active: bool | None = None, limit: int | None = None, offset: int = 0
) -> list[Target]:
    return target_repository.list_targets(db, is_active=is_active, limit=limit, offset=offset)


def get_target_or_raise(db: Session, target_id: uuid.UUID) -> Target:
    target = target_repository.get_target(db, target_id)
    if target is None:
        raise TargetNotFoundError(str(target_id))
    return target


def get_active_target_or_raise(db: Session, target_id: uuid.UUID) -> Target:
    """Same as `get_target_or_raise`, plus an `is_active` gate.

    Only for call sites that launch new work (create_scan,
    trigger_pipeline) — everything else should keep using
    `get_target_or_raise` so reading/listing an inactive target still
    works.
    """
    target = get_target_or_raise(db, target_id)
    if not target.is_active:
        raise TargetInactiveError(str(target_id))
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
    get_target_or_raise(db, target_id)
    active_scans = [
        scan
        for scan in scan_repository.list_scans_for_target(db, target_id)
        if scan.status not in TERMINAL_SCAN_STATUSES
    ]
    if active_scans:
        # Optimistic fast path only, same caveat as this module's own
        # register_target: not atomic with the delete below. The real
        # guard is target_repository.delete_target's own conditional
        # DELETE — this just gives the common (non-racy) case a clear
        # error immediately instead of waiting for that statement's
        # rowcount to say the same thing.
        raise TargetHasActiveScansError(str(target_id))
    deleted = target_repository.delete_target(db, target_id)
    if not deleted:
        # A scan was created in the gap between the check above and this
        # delete (or the target vanished, but get_target_or_raise above
        # already ruled that out moments earlier) - the conditional
        # DELETE's own WHERE clause is what actually caught it.
        raise TargetHasActiveScansError(str(target_id))
