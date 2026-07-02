"""Persistence layer for `Scan` — plain SQLAlchemy queries, no business rules."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from models import Scan, ScanStatus


def create_scan(db: Session, *, target_id: uuid.UUID, triggered_by: str | None) -> Scan:
    scan = Scan(
        target_id=target_id,
        status=ScanStatus.RUNNING,
        triggered_by=triggered_by,
        started_at=datetime.now(UTC),
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


def get_scan(db: Session, scan_id: uuid.UUID) -> Scan | None:
    return db.get(Scan, scan_id)


def complete_scan(
    db: Session, scan: Scan, *, status: ScanStatus, error_message: str | None
) -> Scan:
    scan.status = status
    scan.finished_at = datetime.now(UTC)
    scan.error_message = error_message
    db.commit()
    db.refresh(scan)
    return scan
