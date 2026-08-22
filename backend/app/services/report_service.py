"""Gathers everything a report needs and hands it to the Reports Service.

The Reports Service (Módulo 7) is stateless and has no database access —
this is the one place that assembles a self-contained payload (target +
scan + findings) and pushes it there in a single request, then persists
the resulting `Report` row here, since the Backend is the schema's owner
(same reasoning as every other service integration: Scanner Service in
Módulo 4/5, n8n in Módulo 6).
"""

import re
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

# `file_path` is always generated server-side by the Reports Service as
# "{scan_id}.{ext}" — but it arrives here as an untyped field in an HTTP
# JSON response, not something this service constrains itself. Checked
# once here (write time, when the value is first persisted) and reused by
# the download router (read time) rather than duplicated in both places.
_SAFE_FILENAME = re.compile(r"[A-Za-z0-9._-]+")


def is_safe_filename(value: str) -> bool:
    # `fullmatch` (not `match` + `^...$`) so a trailing "\n" can't sneak
    # through — `$` alone matches immediately before one trailing newline,
    # `fullmatch` requires consuming the entire string.
    return _SAFE_FILENAME.fullmatch(value) is not None


class ReportNotFoundError(Exception):
    """Raised when a report id does not exist."""


class ReportGenerationError(Exception):
    """Raised when the Reports Service can't be reached or fails to render."""


class InvalidReportFilePathError(Exception):
    """Raised when a Report.file_path doesn't look like a filename the
    Reports Service could have generated."""


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
        response = httpx.post(
            f"{settings.reports_base_url}/reports",
            json=payload,
            headers={"X-Internal-Token": settings.internal_api_key},
            timeout=60.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ReportGenerationError(str(exc)) from exc

    # A 200 response doesn't guarantee a well-formed body: the Reports
    # Service being briefly unreachable behind a proxy, or a future schema
    # drift between the two services, could still hand back something that
    # isn't valid JSON or is missing the keys this function expects — none
    # of that is an httpx.HTTPError, so it would otherwise fall straight
    # through as an unhandled 500 instead of the same ReportGenerationError
    # -> 502 path already used for upstream failures above.
    try:
        result = response.json()
        file_path = result["filename"]
        report_format = ReportFormat(result["format"])
    except (ValueError, KeyError) as exc:
        raise ReportGenerationError(f"Reports Service returned an unexpected response: {exc}") from exc

    if not is_safe_filename(file_path):
        raise InvalidReportFilePathError(file_path)
    return report_repository.create_report(
        db,
        scan_id=scan_id,
        format=report_format,
        file_path=file_path,
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
