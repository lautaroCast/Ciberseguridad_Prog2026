"""Endpoints for `scans`, `scan_tasks` ingestion, and `findings` readback.

Scans are created under a target (`POST /targets/{target_id}/scans`);
everything else nests under a scan id. `POST /scans/{scan_id}/tasks` is
Módulo 5's actual entry point: it's the boundary where a Scanner Service
`RawScanResult` becomes normalized `Finding` rows (see
app/services/scan_task_service.py). No per-route try/except here — domain
exceptions (ScanNotFoundError, TargetNotFoundError, ...) are translated to
HTTP responses by the handlers registered once in app/main.py.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.finding import FindingRead
from app.schemas.scan import ScanComplete, ScanCreate, ScanRead
from app.schemas.scan_task import ScanTaskIngest, ScanTaskIngestResult, ScanTaskRead
from app.services import finding_service, pipeline_service, scan_service, scan_task_service
from models import ScanStatus

router = APIRouter(tags=["scans"])

_COMPLETE_STATUS_MAP: dict[str, ScanStatus] = {
    "completed": ScanStatus.COMPLETED,
    "failed": ScanStatus.FAILED,
}


@router.post(
    "/targets/{target_id}/scans", response_model=ScanRead, status_code=status.HTTP_201_CREATED
)
def create_scan(
    target_id: uuid.UUID, payload: ScanCreate, db: Session = Depends(get_db)
) -> ScanRead:
    return scan_service.create_scan(db, target_id=target_id, triggered_by=payload.triggered_by)


@router.post(
    "/targets/{target_id}/pipeline", response_model=ScanRead, status_code=status.HTTP_202_ACCEPTED
)
def trigger_pipeline(target_id: uuid.UUID, db: Session = Depends(get_db)) -> ScanRead:
    """Starts the full n8n pipeline (Módulo 6) for a target.

    Returns as soon as n8n acknowledges the trigger (n8n's Webhook node
    responds immediately, before running the workflow) — the scan is
    `running` in the response, not `completed`. Poll `GET /scans/{id}` or
    `GET /scans/{id}/findings` for progress.
    """
    return pipeline_service.trigger_pipeline(db, target_id)


@router.get("/scans/{scan_id}", response_model=ScanRead)
def get_scan(scan_id: uuid.UUID, db: Session = Depends(get_db)) -> ScanRead:
    return scan_service.get_scan_or_raise(db, scan_id)


@router.post("/scans/{scan_id}/complete", response_model=ScanRead)
def complete_scan(
    scan_id: uuid.UUID, payload: ScanComplete, db: Session = Depends(get_db)
) -> ScanRead:
    return scan_service.complete_scan(
        db,
        scan_id,
        status=_COMPLETE_STATUS_MAP[payload.status],
        error_message=payload.error_message,
    )


@router.post(
    "/scans/{scan_id}/tasks",
    response_model=ScanTaskIngestResult,
    status_code=status.HTTP_201_CREATED,
)
def ingest_scan_task(
    scan_id: uuid.UUID, payload: ScanTaskIngest, db: Session = Depends(get_db)
) -> ScanTaskIngestResult:
    result = scan_task_service.ingest_scan_task(
        db,
        scan_id,
        tool=payload.tool,
        command=payload.command,
        status=payload.status,
        started_at=payload.started_at,
        finished_at=payload.finished_at,
        raw_output=payload.raw_output,
        parsed=payload.parsed,
        error_message=payload.error_message,
    )
    return ScanTaskIngestResult(
        scan_task=ScanTaskRead.model_validate(result.scan_task),
        services_upserted=result.services_upserted,
        technologies_created=result.technologies_created,
        findings_created=result.findings_created,
    )


@router.get("/scans/{scan_id}/findings", response_model=list[FindingRead])
def list_findings(scan_id: uuid.UUID, db: Session = Depends(get_db)) -> list[FindingRead]:
    return finding_service.list_findings_for_scan(db, scan_id)
