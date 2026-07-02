"""Ingests a Scanner Service `RawScanResult` and normalizes it into rows.

This is Módulo 5's core: everything the Scanner Service (Módulo 4) hands
back as tool-specific `parsed` JSON gets turned, here, into the same
`services` / `technologies` / `findings` shape regardless of which of the
five tools produced it (see `app/normalization/`). The whole ingest — the
`ScanTask` row plus every `Service`/`Technology`/`Finding`/`CveReference`
row it normalizes into — commits as a single transaction, so a scan_task
that made it into the DB always has its normalized rows alongside it,
never a partial result.

A normalization failure (unexpected shape from a tool, a normalizer bug)
is recorded on the scan_task's `error_message` rather than raised: the
raw scan result is still valuable on its own even if it couldn't be
turned into structured findings, so ingestion must not 500 just because
normalization did.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.normalization.registry import get_normalizer
from app.repositories import (
    finding_repository,
    scan_task_repository,
    service_repository,
    technology_repository,
)
from app.services.scan_service import get_scan_or_raise
from models import ScanTask, ScanTaskStatus

_STATUS_MAP: dict[str, ScanTaskStatus] = {
    "completed": ScanTaskStatus.COMPLETED,
    "failed": ScanTaskStatus.FAILED,
}


@dataclass
class IngestResult:
    scan_task: ScanTask
    services_upserted: int
    technologies_created: int
    findings_created: int


def ingest_scan_task(
    db: Session,
    scan_id: uuid.UUID,
    *,
    tool: str,
    command: str,
    status: str,
    started_at: datetime,
    finished_at: datetime,
    raw_output: str,
    parsed: Any | None,
    error_message: str | None,
) -> IngestResult:
    get_scan_or_raise(db, scan_id)  # 404s before writing anything if the scan doesn't exist

    scan_task = scan_task_repository.create_scan_task(
        db,
        scan_id=scan_id,
        tool_name=tool,
        status=_STATUS_MAP[status],
        command=command,
        raw_output=raw_output,
        started_at=started_at,
        finished_at=finished_at,
        error_message=error_message,
    )

    services_upserted = technologies_created = findings_created = 0

    normalizer = get_normalizer(tool) if status == "completed" and parsed is not None else None
    if normalizer is not None:
        try:
            normalized = normalizer(parsed)
        except Exception as exc:  # noqa: BLE001 — a bad normalizer input shouldn't 500 the ingest
            note = f"Normalization failed: {exc}"
            scan_task.error_message = (
                f"{scan_task.error_message}; {note}" if scan_task.error_message else note
            )
        else:
            for svc in normalized.services:
                service_repository.get_or_create_service(
                    db,
                    scan_id=scan_id,
                    host=svc.host,
                    port=svc.port,
                    protocol=svc.protocol,
                    service_name=svc.service_name,
                    product=svc.product,
                    version=svc.version,
                )
                services_upserted += 1

            for tech in normalized.technologies:
                technology_repository.create_technology(
                    db,
                    scan_id=scan_id,
                    name=tech.name,
                    detected_by=tech.detected_by,
                    version=tech.version,
                    category=tech.category,
                    confidence=tech.confidence,
                )
                technologies_created += 1

            for finding in normalized.findings:
                finding_row = finding_repository.create_finding(
                    db,
                    scan_id=scan_id,
                    scan_task_id=scan_task.id,
                    service_id=None,
                    title=finding.title,
                    description=finding.description,
                    finding_type=finding.finding_type,
                    evidence=finding.evidence,
                    confidence=finding.confidence,
                    cvss_score=finding.cvss_score,
                    cvss_vector=finding.cvss_vector,
                    severity=finding.severity,
                )
                findings_created += 1
                for cve in finding.cve_references:
                    finding_repository.create_cve_reference(
                        db,
                        finding_id=finding_row.id,
                        cve_id=cve.cve_id,
                        cvss_score=cve.cvss_score,
                        cvss_vector=cve.cvss_vector,
                        description=cve.description,
                        source_url=cve.source_url,
                    )

    db.commit()
    db.refresh(scan_task)
    return IngestResult(
        scan_task=scan_task,
        services_upserted=services_upserted,
        technologies_created=technologies_created,
        findings_created=findings_created,
    )
