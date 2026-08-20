"""Business rules for `scans`.

A `Scan` always belongs to an already-registered, whitelisted `Target` —
creating one re-validates the target exists (via target_service, not a
duplicated check) rather than trusting the id blindly.
"""

import uuid

from sqlalchemy.orm import Session

from app.repositories import scan_repository
from app.services import target_service
from models import Scan, ScanStatus


_TERMINAL_STATUSES = frozenset({ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED})


class ScanNotFoundError(Exception):
    """Raised when a scan id does not exist."""


class ScanAlreadyTerminalError(Exception):
    """Raised when POST /scans/{id}/complete targets a scan that already
    reached a terminal status — nothing calls this twice by design today
    (n8n's Complete Scan node runs once per pipeline), so a repeat call is
    treated as a conflict rather than silently overwriting the first
    outcome."""


def create_scan(db: Session, *, target_id: uuid.UUID, triggered_by: str | None) -> Scan:
    target_service.get_active_target_or_raise(db, target_id)
    return scan_repository.create_scan(db, target_id=target_id, triggered_by=triggered_by)


def list_scans_for_target(db: Session, target_id: uuid.UUID) -> list[Scan]:
    target_service.get_target_or_raise(db, target_id)
    return scan_repository.list_scans_for_target(db, target_id)


def get_scan_or_raise(db: Session, scan_id: uuid.UUID) -> Scan:
    scan = scan_repository.get_scan(db, scan_id)
    if scan is None:
        raise ScanNotFoundError(str(scan_id))
    return scan


def complete_scan(
    db: Session, scan_id: uuid.UUID, *, status: ScanStatus, error_message: str | None
) -> Scan:
    scan = get_scan_or_raise(db, scan_id)
    if scan.status in _TERMINAL_STATUSES:
        raise ScanAlreadyTerminalError(str(scan_id))
    return scan_repository.complete_scan(db, scan, status=status, error_message=error_message)
