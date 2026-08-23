"""Persistence layer for `Finding` and `CveReference`."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import CveReference, Finding, SeverityLevel

# Tool-derived strings have no length guarantee; these columns are bounded
# (database/models/finding.py, cve_reference.py) — truncate here, once,
# rather than trusting every one of the 5 normalizers to do it themselves
# (only `title` currently gets that treatment, at the normalizer level).
_FINDING_TYPE_MAX = 100
_CONFIDENCE_MAX = 20
_CVSS_VECTOR_MAX = 100
_CVE_ID_MAX = 20
_SOURCE_URL_MAX = 500


def _truncate(value: str | None, max_length: int) -> str | None:
    return value[:max_length] if value is not None else None


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
        finding_type=finding_type[:_FINDING_TYPE_MAX],
        evidence=evidence,
        confidence=_truncate(confidence, _CONFIDENCE_MAX),
        cvss_score=cvss_score,
        cvss_vector=_truncate(cvss_vector, _CVSS_VECTOR_MAX),
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
        cve_id=cve_id[:_CVE_ID_MAX],
        cvss_score=cvss_score,
        cvss_vector=_truncate(cvss_vector, _CVSS_VECTOR_MAX),
        description=description,
        source_url=_truncate(source_url, _SOURCE_URL_MAX),
    )
    db.add(reference)
    db.flush()
    return reference


def list_findings_for_scan(db: Session, scan_id: uuid.UUID) -> list[Finding]:
    stmt = select(Finding).where(Finding.scan_id == scan_id).order_by(Finding.created_at.desc())
    return list(db.execute(stmt).scalars().all())
