"""Persistence layer for `Report` — plain SQLAlchemy queries, no business rules."""

import uuid

from models import Report, ReportFormat
from sqlalchemy import select
from sqlalchemy.orm import Session


def create_report(
    db: Session,
    *,
    scan_id: uuid.UUID,
    format: ReportFormat,
    file_path: str,
    generated_by: str | None,
) -> Report:
    report = Report(scan_id=scan_id, format=format, file_path=file_path, generated_by=generated_by)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: uuid.UUID) -> Report | None:
    return db.get(Report, report_id)


def get_report_by_scan_and_format(
    db: Session, scan_id: uuid.UUID, format: ReportFormat
) -> Report | None:
    """Backs the idempotent-replay path in report_service.generate_report -
    looked up only after create_report's insert hits the unique
    (scan_id, format) index, to return the row a retried Generate Report
    call already created instead of duplicating it. Same idiom as
    scan_task_repository.get_scan_task_by_scan_and_tool."""
    stmt = select(Report).where(Report.scan_id == scan_id, Report.format == format)
    return db.scalars(stmt).first()


def list_reports_for_scan(
    db: Session, scan_id: uuid.UUID, *, limit: int | None = None, offset: int = 0
) -> list[Report]:
    stmt = (
        select(Report)
        .where(Report.scan_id == scan_id)
        .order_by(Report.generated_at.desc())
        .offset(offset)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())
