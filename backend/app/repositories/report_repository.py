"""Persistence layer for `Report` — plain SQLAlchemy queries, no business rules."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Report, ReportFormat


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


def list_reports_for_scan(db: Session, scan_id: uuid.UUID) -> list[Report]:
    stmt = select(Report).where(Report.scan_id == scan_id).order_by(Report.generated_at.desc())
    return list(db.execute(stmt).scalars().all())
