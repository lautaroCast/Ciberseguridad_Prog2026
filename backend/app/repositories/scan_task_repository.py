"""Persistence layer for `ScanTask`.

`create_scan_task` deliberately does not commit: it's always called from
`app/services/scan_task_service.py` as the first step of a single
transaction that also writes every `Service`/`Technology`/`Finding` row
the scan_task's output normalizes into — a scan_task that reaches the DB
always has its normalized rows alongside it, never a partial result.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import ScanTask, ScanTaskStatus


def create_scan_task(
    db: Session,
    *,
    scan_id: uuid.UUID,
    tool_name: str,
    status: ScanTaskStatus,
    command: str | None,
    raw_output: str | None,
    started_at: datetime | None,
    finished_at: datetime | None,
    error_message: str | None,
) -> ScanTask:
    scan_task = ScanTask(
        scan_id=scan_id,
        tool_name=tool_name,
        status=status,
        command=command,
        raw_output=raw_output,
        started_at=started_at,
        finished_at=finished_at,
        error_message=error_message,
    )
    db.add(scan_task)
    db.flush()  # assigns scan_task.id so findings below can reference it
    return scan_task


def list_scan_tasks_for_scan(db: Session, scan_id: uuid.UUID) -> list[ScanTask]:
    stmt = select(ScanTask).where(ScanTask.scan_id == scan_id).order_by(ScanTask.created_at)
    return list(db.scalars(stmt))


def get_scan_task_by_scan_and_tool(
    db: Session, scan_id: uuid.UUID, tool_name: str
) -> ScanTask | None:
    """Backs the idempotent-replay path in scan_task_service.ingest_scan_task
    - looked up only after create_scan_task's insert hits the unique
    (scan_id, tool_name) index, to return the row a retried ingest already
    created instead of duplicating it."""
    stmt = select(ScanTask).where(
        ScanTask.scan_id == scan_id, ScanTask.tool_name == tool_name
    )
    return db.scalars(stmt).first()
