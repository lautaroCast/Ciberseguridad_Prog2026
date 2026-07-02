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
from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.report import ReportRead
from app.services import report_service

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
def list_reports(scan_id: uuid.UUID, db: Session = Depends(get_db)) -> list[ReportRead]:
    return report_service.list_reports_for_scan(db, scan_id)


@router.get("/reports/{report_id}/download")
def download_report(report_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    report = report_service.get_report_or_raise(db, report_id)
    settings = get_settings()
    url = f"{settings.reports_base_url}/reports/{report.file_path}"
    try:
        upstream = httpx.get(url, timeout=30.0)
    except httpx.HTTPError as exc:
        raise ReportFileUnavailableError(str(exc)) from exc
    if upstream.status_code == 404:
        raise ReportFileUnavailableError(report.file_path)
    upstream.raise_for_status()

    media_type = _MEDIA_TYPES.get(report.format.value, "application/octet-stream")
    return Response(
        content=upstream.content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{report.file_path}"'},
    )
