"""Business rules for `scans`.

A `Scan` always belongs to an already-registered, whitelisted `Target` —
creating one re-validates the target exists (via target_service, not a
duplicated check) rather than trusting the id blindly.
"""

import uuid

from models import TERMINAL_SCAN_STATUSES, Scan, ScanStatus
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories import scan_repository
from app.services import target_service

# Re-exported under this module's established public name: pipeline_service.py
# (and target_service.py's delete_target guard) import the same object
# instead of each defining their own copy, which is what keeps them from
# silently drifting apart. The canonical definition lives in
# database/models/enums.py, next to the ScanStatus enum it classifies —
# moved there once a third module (target_service) needed it too, since
# scan_service already imports target_service and importing it back the
# other way would cycle.
TERMINAL_STATUSES = TERMINAL_SCAN_STATUSES


class ScanNotFoundError(Exception):
    """Raised when a scan id does not exist."""


class ScanAlreadyTerminalError(Exception):
    """Raised when a scan that's already terminal is targeted with a
    completion that conflicts with its current status - `POST
    /scans/{id}/complete` asking for a *different* status than the one
    already persisted, or `ingest_scan_task` attaching new rows to a scan
    that finished in the meantime.

    A completion that matches the status already persisted (n8n's
    `Complete Scan` node retrying after its own response was lost/timed
    out, `retryOnFail: true`) is not this case - `complete_scan` below
    treats that as an idempotent repeat and returns the existing scan
    instead of raising this."""


class ScanAlreadyRunningError(Exception):
    """Raised when a target's host already has a non-terminal scan and a
    new one is requested. The real guard is `ix_scans_one_active_per_host`,
    a partial unique index on `scans.host` — this exception is what an
    `IntegrityError` from that index gets translated into, same idiom as
    `target_service.register_target`'s own unique-constraint catch.

    2026-09-06 correction round: re-keyed from `target_id` to `host` — two
    different `Target` rows can point at the same physical host, and the
    conflicting non-terminal scan this error reports may belong to a
    sibling target sharing that host, not necessarily the one just
    requested."""


def create_scan(db: Session, *, target_id: uuid.UUID, triggered_by: str | None) -> Scan:
    target = target_service.get_active_target_or_raise(db, target_id)
    try:
        return scan_repository.create_scan(
            db, target_id=target_id, host=target.host, triggered_by=triggered_by
        )
    except IntegrityError as exc:
        db.rollback()
        # An IntegrityError here is usually the host-concurrency race that
        # ix_scans_one_active_per_host guards against — but if `target` was
        # deleted between get_active_target_or_raise above and this
        # insert's commit, the FK violation looks identical. Re-checking
        # existence disambiguates: it raises TargetNotFoundError on its own
        # if the target is gone, so ScanAlreadyRunningError only survives
        # to describe the case it actually names.
        target_service.get_target_or_raise(db, target_id)
        raise ScanAlreadyRunningError(str(target_id)) from exc


def list_scans_for_target(
    db: Session, target_id: uuid.UUID, *, limit: int | None = None, offset: int = 0
) -> list[Scan]:
    target_service.get_target_or_raise(db, target_id)
    return scan_repository.list_scans_for_target(db, target_id, limit=limit, offset=offset)


def get_scan_or_raise(db: Session, scan_id: uuid.UUID) -> Scan:
    scan = scan_repository.get_scan(db, scan_id)
    if scan is None:
        raise ScanNotFoundError(str(scan_id))
    return scan


def get_scan_for_update_or_raise(db: Session, scan_id: uuid.UUID) -> Scan:
    """Same as `get_scan_or_raise`, but locks the row for the rest of the
    caller's transaction. Only `scan_task_service.ingest_scan_task` should
    use this - every other caller just reads, and locking on a plain read
    would serialize requests that don't need it."""
    scan = scan_repository.get_scan_for_update(db, scan_id)
    if scan is None:
        raise ScanNotFoundError(str(scan_id))
    return scan


def complete_scan(
    db: Session,
    scan_id: uuid.UUID,
    *,
    status: ScanStatus,
    error_message: str | None,
    pipeline_run_id: str | None = None,
) -> Scan:
    scan = get_scan_or_raise(db, scan_id)
    if scan.status in TERMINAL_STATUSES:
        if scan.status == status:
            # Idempotent retry: an earlier attempt already committed this
            # exact completion but its response was lost/timed out before
            # n8n saw it (Complete Scan's own retryOnFail) - same status
            # means same completion, so return the current state instead
            # of a conflict. A *different* status (e.g. a stray retry
            # after the scan already failed a different way) is still a
            # real conflict, handled below.
            return scan
        # Optimistic fast path only, same caveat as target_service.
        # register_target's own pre-check: not atomic with the write
        # below. The real guard is the conditional UPDATE's WHERE clause
        # inside scan_repository.complete_scan.
        raise ScanAlreadyTerminalError(str(scan_id))
    updated = scan_repository.complete_scan(
        db,
        scan_id,
        status=status,
        error_message=error_message,
        pipeline_run_id=pipeline_run_id,
        forbidden_statuses=TERMINAL_STATUSES,
    )
    if updated is None:
        # Lost the race between the pre-check above and the conditional
        # UPDATE - a concurrent completion landed in between. Re-fetch and
        # apply the exact same idempotent-retry rule as the pre-check.
        current = get_scan_or_raise(db, scan_id)
        if current.status == status:
            return current
        raise ScanAlreadyTerminalError(str(scan_id))
    return updated
