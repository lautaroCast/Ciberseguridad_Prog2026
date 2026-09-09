"""Triggers the n8n pipeline (Módulo 6) for a registered target.

This is the only place the Backend talks to n8n, and it only ever pushes
one HTTP request: a `Scan` row is created here (reusing the same
`scan_repository` Módulo 5 already established), then n8n's Webhook
trigger is notified with just enough context (`scan_id`, `target_id`,
`host`) to run the rest of the pipeline on its own, calling back into the
Backend's own `/scans/{id}/tasks` and `/scans/{id}/complete` endpoints as
it goes. The Backend never waits for the pipeline to finish — n8n's
webhook responds immediately, right after checking the shared
`X-Webhook-Secret` header (see the `Check Webhook Secret` node in
n8n/workflows/vulnscan-pipeline.json), so this call returns in well under
a second regardless of how long the scan itself takes.
"""

import uuid

import httpx
from models import Scan, ScanStatus
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.repositories import scan_repository
from app.services import target_service
from app.services.scan_service import TERMINAL_STATUSES, ScanAlreadyRunningError


class PipelineTriggerError(Exception):
    """Raised when n8n's webhook can't be reached or rejects the trigger."""


def trigger_pipeline(db: Session, target_id: uuid.UUID) -> Scan:
    target = target_service.get_active_target_or_raise(db, target_id)
    try:
        scan = scan_repository.create_scan(
            db, target_id=target_id, host=target.host, triggered_by="n8n-pipeline"
        )
    except IntegrityError as exc:
        # Real guard is ix_scans_one_active_per_host - see
        # ScanAlreadyRunningError's own docstring for why this isn't just an
        # optimistic pre-check. But the same IntegrityError also fires if
        # `target` was deleted between get_active_target_or_raise above and
        # this insert's commit (scans.target_id's FK) - re-checking
        # existence disambiguates: it raises TargetNotFoundError on its own
        # if the target is gone, so ScanAlreadyRunningError only survives to
        # describe the case it actually names.
        db.rollback()
        target_service.get_target_or_raise(db, target_id)
        raise ScanAlreadyRunningError(str(target_id)) from exc

    settings = get_settings()
    payload = {"scan_id": str(scan.id), "target_id": str(target_id), "host": target.host}
    try:
        response = httpx.post(
            settings.n8n_pipeline_webhook_url,
            json=payload,
            headers={"X-Webhook-Secret": settings.n8n_webhook_secret},
            timeout=10.0,
        )
        response.raise_for_status()
    except (httpx.ReadTimeout, httpx.WriteTimeout) as exc:
        # Unlike ConnectTimeout/ConnectError (siblings under
        # httpx.TransportError, not parent/child - request never left this
        # process), a ReadTimeout means the request body reached n8n in
        # full: n8n may already have started the pipeline and be writing
        # real scan_task/finding rows against this scan. WriteTimeout is
        # ReadTimeout's sibling under TimeoutException, not ConnectTimeout's
        # - the payload may have gone out partially or fully before the
        # write itself timed out, same ambiguity. (httpx.PoolTimeout, in
        # contrast, is deliberately left out of this branch: it means no
        # connection was ever acquired to write to, and is unreachable
        # here anyway since httpx.post() builds a fresh one-off client per
        # call with no pool shared across requests.) Marking FAILED here
        # would leave those writes targeting a scan the Backend already
        # considers dead — leave it RUNNING; the caller only learns the
        # trigger call's own outcome is unknown.
        raise PipelineTriggerError(
            f"n8n did not respond in time — the pipeline may have already started: {exc}"
        ) from exc
    except httpx.HTTPError as exc:
        # Every other HTTPError here (ConnectError/ConnectTimeout, a
        # non-2xx from raise_for_status()) means the request never reached
        # n8n or n8n explicitly rejected it - unlike ReadTimeout above,
        # nothing downstream can be running. The scan row already exists
        # but nothing will ever process it — mark it failed immediately
        # rather than leaving a "running" scan that silently never
        # progresses.
        scan_repository.complete_scan(
            db,
            scan.id,
            status=ScanStatus.FAILED,
            error_message=f"Failed to trigger n8n pipeline: {exc}",
            forbidden_statuses=TERMINAL_STATUSES,
        )
        raise PipelineTriggerError(str(exc)) from exc

    return scan
