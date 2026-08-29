"""Persistence layer for `Scan` — plain SQLAlchemy queries, no business rules."""

import uuid
from datetime import UTC, datetime
from typing import Iterable

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models import Scan, ScanStatus


def list_scans_for_target(
    db: Session, target_id: uuid.UUID, *, limit: int | None = None, offset: int = 0
) -> list[Scan]:
    stmt = (
        select(Scan)
        .where(Scan.target_id == target_id)
        .order_by(Scan.created_at.desc())
        .offset(offset)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())


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
    db: Session,
    scan_id: uuid.UUID,
    *,
    status: ScanStatus,
    error_message: str | None,
    forbidden_statuses: Iterable[ScanStatus],
    pipeline_run_id: str | None = None,
) -> Scan | None:
    """Atomically transitions a scan to a terminal status — but only if its
    *current* status (checked by the database, in the same statement that
    writes the new one) isn't already one of `forbidden_statuses`.

    A previous version read the scan, checked its status in Python, and
    only then wrote the update — two concurrent completions of the same
    scan (e.g. a retried webhook call) could both read a non-terminal
    status before either commits, so the "only completes once" guarantee
    wasn't actually enforced under concurrency. Same "let the database be
    the source of truth, not a prior SELECT" idea already used elsewhere
    in this codebase (target_service.register_target's real guard is the
    table's own unique constraint; service_repository.get_or_create_service
    is insert-first + catch the conflict) — here the guard is a
    conditional UPDATE instead, since a status-transition rule doesn't
    have a schema-level constraint to lean on the way a uniqueness rule
    does.

    Returns None if no row matched (the scan doesn't exist, or it was
    already in one of `forbidden_statuses`) — the caller decides what
    that means.
    """
    values: dict[str, object] = {
        "status": status,
        "finished_at": datetime.now(UTC),
        "error_message": error_message,
    }
    if pipeline_run_id is not None:
        values["pipeline_run_id"] = pipeline_run_id

    stmt = (
        update(Scan)
        .where(Scan.id == scan_id, Scan.status.not_in(forbidden_statuses))
        .values(**values)
    )
    result = db.execute(stmt)
    if result.rowcount == 0:
        db.rollback()
        return None
    db.commit()
    return db.get(Scan, scan_id)
