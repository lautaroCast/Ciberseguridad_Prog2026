"""Triggers the n8n pipeline (Módulo 6) for a registered target.

This is the only place the Backend talks to n8n, and it only ever pushes
one HTTP request: a `Scan` row is created here (reusing the same
`scan_repository` Módulo 5 already established), then n8n's Webhook
trigger is notified with just enough context (`scan_id`, `target_id`,
`host`) to run the rest of the pipeline on its own, calling back into the
Backend's own `/scans/{id}/tasks` and `/scans/{id}/complete` endpoints as
it goes. The Backend never waits for the pipeline to finish — n8n's
webhook responds immediately (see the trigger node's `responseMode` in
n8n/workflows/vulnscan-pipeline.json), so this call returns in well under
a second regardless of how long the scan itself takes.
"""

import uuid

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.repositories import scan_repository
from app.services import target_service
from models import Scan, ScanStatus


class PipelineTriggerError(Exception):
    """Raised when n8n's webhook can't be reached or rejects the trigger."""


def trigger_pipeline(db: Session, target_id: uuid.UUID) -> Scan:
    target = target_service.get_target_or_raise(db, target_id)
    scan = scan_repository.create_scan(db, target_id=target_id, triggered_by="n8n-pipeline")

    settings = get_settings()
    payload = {"scan_id": str(scan.id), "target_id": str(target_id), "host": target.host}
    try:
        response = httpx.post(settings.n8n_pipeline_webhook_url, json=payload, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        # The scan row already exists but nothing will ever process it —
        # mark it failed immediately rather than leaving a "running" scan
        # that silently never progresses.
        scan_repository.complete_scan(
            db, scan, status=ScanStatus.FAILED, error_message=f"Failed to trigger n8n pipeline: {exc}"
        )
        raise PipelineTriggerError(str(exc)) from exc

    return scan
