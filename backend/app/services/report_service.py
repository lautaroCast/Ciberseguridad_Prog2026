"""Gathers everything a report needs and hands it to the Reports Service.

The Reports Service (Módulo 7) is stateless and has no database access —
this is the one place that assembles a self-contained payload (target +
scan + findings) and pushes it there in a single request, then persists
the resulting `Report` row here, since the Backend is the schema's owner
(same reasoning as every other service integration: Scanner Service in
Módulo 4/5, n8n in Módulo 6).
"""

import uuid

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.repositories import report_repository
from app.schemas.finding import FindingRead
from app.schemas.scan import ScanRead
from app.schemas.target import TargetRead
from app.services import finding_service, scan_service, target_service
from models import Report, ReportFormat


class ReportNotFoundError(Exception):
    """Raised when a report id does not exist."""


class ReportGenerationError(Exception):
    """Raised when the Reports Service can't be reached or fails to render."""


def generate_report(db: Session, scan_id: uuid.UUID, format: str) -> Report:
    scan = scan_service.get_scan_or_raise(db, scan_id)
    target = target_service.get_target_or_raise(db, scan.target_id)
    findings = finding_service.list_findings_for_scan(db, scan_id)

    payload = {
        "format": format,
        "target": TargetRead.model_validate(target).model_dump(mode="json"),
        "scan": ScanRead.model_validate(scan).model_dump(mode="json"),
        "findings": [
            FindingRead.model_validate(finding).model_dump(mode="json") for finding in findings
        ],
    }

    settings = get_settings()
    try:
        response = httpx.post(f"{settings.reports_base_url}/reports", json=payload, timeout=60.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ReportGenerationError(str(exc)) from exc

    result = response.json()
    return report_repository.create_report(
        db,
        scan_id=scan_id,
        format=ReportFormat(result["format"]),
        file_path=result["filename"],
        generated_by="backend",
    )


def list_reports_for_scan(db: Session, scan_id: uuid.UUID) -> list[Report]:
    scan_service.get_scan_or_raise(db, scan_id)  # 404s for an unknown scan instead of returning []
    return report_repository.list_reports_for_scan(db, scan_id)


def get_report_or_raise(db: Session, report_id: uuid.UUID) -> Report:
    report = report_repository.get_report(db, report_id)
    if report is None:
        raise ReportNotFoundError(str(report_id))
    return report
