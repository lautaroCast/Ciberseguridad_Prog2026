"""Persistence layer for `Finding` and `CveReference`."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import CveReference, Finding, SeverityLevel


def create_finding(
    db: Session,
    *,
    scan_id: uuid.UUID,
    scan_task_id: uuid.UUID,
    service_id: uuid.UUID | None,
    title: str,
    description: str | None,
    finding_type: str,
    evidence: str | None,
    confidence: str | None,
    cvss_score: float | None,
    cvss_vector: str | None,
    severity: SeverityLevel,
) -> Finding:
    finding = Finding(
        scan_id=scan_id,
        scan_task_id=scan_task_id,
        service_id=service_id,
        title=title,
        description=description,
        finding_type=finding_type,
        evidence=evidence,
        confidence=confidence,
        cvss_score=cvss_score,
        cvss_vector=cvss_vector,
        severity=severity,
    )
    db.add(finding)
    db.flush()
    return finding


def create_cve_reference(
    db: Session,
    *,
    finding_id: uuid.UUID,
    cve_id: str,
    cvss_score: float | None,
    cvss_vector: str | None,
    description: str | None,
    source_url: str | None,
) -> CveReference:
    reference = CveReference(
        finding_id=finding_id,
        cve_id=cve_id,
        cvss_score=cvss_score,
        cvss_vector=cvss_vector,
        description=description,
        source_url=source_url,
    )
    db.add(reference)
    db.flush()
    return reference


def list_findings_for_scan(db: Session, scan_id: uuid.UUID) -> list[Finding]:
    stmt = select(Finding).where(Finding.scan_id == scan_id).order_by(Finding.created_at.desc())
    return list(db.execute(stmt).scalars().all())
