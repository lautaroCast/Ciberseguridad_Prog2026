"""Endpoints for report generation, listing, and download.

`GET /reports/{report_id}/download` proxies the file from the Reports
Service rather than reading it off a shared volume — the two services
don't share filesystem access (same "nothing but the DB is shared, and
only the Backend touches that" boundary used everywhere else in this
architecture), so this is a plain HTTP passthrough, not a redirect.
"""

import uuid
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.report import ReportRead
from app.services import report_service
from app.services.report_service import InvalidReportFilePathError, is_safe_filename

router = APIRouter(tags=["reports"])

_MEDIA_TYPES = {
    "pdf": "application/pdf",
    "html": "text/html",
    "markdown": "text/markdown",
    "json": "application/json",
}


class ReportFileUnavailableError(Exception):
    """Raised when the Reports Service no longer has the file on disk."""


@router.post(
    "/scans/{scan_id}/reports", response_model=ReportRead, status_code=status.HTTP_201_CREATED
)
def create_report(
    scan_id: uuid.UUID,
    format: Literal["pdf", "html", "markdown", "json"],
    db: Session = Depends(get_db),
) -> ReportRead:
    return report_service.generate_report(db, scan_id, format)


@router.get("/scans/{scan_id}/reports", response_model=list[ReportRead])
def list_reports(
    scan_id: uuid.UUID,
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ReportRead]:
    return report_service.list_reports_for_scan(db, scan_id, limit=limit, offset=offset)


@router.get("/reports/{report_id}/download")
def download_report(report_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    report = report_service.get_report_or_raise(db, report_id)
    if not is_safe_filename(report.file_path):
        raise InvalidReportFilePathError(report.file_path)
    settings = get_settings()
    url = f"{settings.reports_base_url}/reports/{report.file_path}"
    try:
        upstream = httpx.get(
            url, headers={"X-Internal-Token": settings.internal_api_key}, timeout=30.0
        )
        if upstream.status_code == 404:
            raise ReportFileUnavailableError(report.file_path)
        upstream.raise_for_status()
    except httpx.HTTPError as exc:
        raise ReportFileUnavailableError(str(exc)) from exc

    media_type = _MEDIA_TYPES.get(report.format.value, "application/octet-stream")
    return Response(
        content=upstream.content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{report.file_path}"'},
    )
