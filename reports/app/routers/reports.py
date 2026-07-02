"""Endpoints for report generation and file download.

This service is stateless: it has no database of its own, no knowledge of
`scan_id`/`target_id` beyond what's in the request body, and no auth of
its own — it trusts the Backend (the only caller in this architecture) to
have already validated everything. The Backend persists the resulting
`Report` row; this service only ever produces and serves bytes on disk.
"""

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.config import Settings, get_settings
from app.schemas.report import ReportRequest, ReportResult
from app.services import report_generator

router = APIRouter(tags=["reports"])

_MEDIA_TYPES = {
    "pdf": "application/pdf",
    "html": "text/html",
    "md": "text/markdown",
    "json": "application/json",
}


class ReportFileNotFoundError(Exception):
    """Raised when a requested report filename doesn't exist on disk."""


@router.post("/reports", response_model=ReportResult)
def create_report(
    payload: ReportRequest, settings: Settings = Depends(get_settings)
) -> ReportResult:
    return report_generator.generate(payload, Path(settings.reports_output_dir))


@router.get("/reports/{filename}")
def download_report(filename: str, settings: Settings = Depends(get_settings)) -> FileResponse:
    output_dir = Path(settings.reports_output_dir).resolve()
    # `filename` is caller-controlled input reflected straight into a
    # filesystem path — resolve and re-check it's still inside
    # output_dir before touching disk, so "../../etc/passwd"-style values
    # can't escape the reports directory.
    candidate = (output_dir / filename).resolve()
    if output_dir not in candidate.parents or not candidate.is_file():
        raise ReportFileNotFoundError(filename)

    extension = candidate.suffix.lstrip(".")
    media_type = _MEDIA_TYPES.get(extension, "application/octet-stream")
    return FileResponse(candidate, media_type=media_type, filename=candidate.name)
