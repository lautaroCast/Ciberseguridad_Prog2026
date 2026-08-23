"""create_cve_reference truncates cve_id/cvss_vector before insert but had
been leaving source_url (String(500), database/models/cve_reference.py)
unguarded — the one field in this function that didn't follow the same
pattern the rest of it already uses."""

from datetime import UTC, datetime

from app.repositories import finding_repository, scan_task_repository
from app.services import scan_service, target_service
from models import ScanTaskStatus, SeverityLevel


def _make_scan_task(db_session):
    target = target_service.register_target(
        db_session, name="juice-shop-demo", host="juice-shop", description=None
    )
    scan = scan_service.create_scan(db_session, target_id=target.id, triggered_by=None)
    now = datetime.now(UTC)
    return scan_task_repository.create_scan_task(
        db_session,
        scan_id=scan.id,
        tool_name="nuclei",
        status=ScanTaskStatus.COMPLETED,
        command="nuclei -u http://juice-shop",
        raw_output="{}",
        started_at=now,
        finished_at=now,
        error_message=None,
    )


def _make_finding(db_session, scan_task):
    return finding_repository.create_finding(
        db_session,
        scan_id=scan_task.scan_id,
        scan_task_id=scan_task.id,
        service_id=None,
        title="Exposed Admin Panel",
        description=None,
        finding_type="template-match",
        evidence=None,
        confidence=None,
        cvss_score=None,
        cvss_vector=None,
        severity=SeverityLevel.HIGH,
    )


def test_create_cve_reference_truncates_source_url(db_session):
    scan_task = _make_scan_task(db_session)
    finding = _make_finding(db_session, scan_task)

    reference = finding_repository.create_cve_reference(
        db_session,
        finding_id=finding.id,
        cve_id="CVE-2024-12345",
        cvss_score=None,
        cvss_vector=None,
        description=None,
        source_url="https://example.com/" + ("a" * 500),
    )

    assert len(reference.source_url) == 500


def test_create_cve_reference_allows_none_source_url(db_session):
    scan_task = _make_scan_task(db_session)
    finding = _make_finding(db_session, scan_task)

    reference = finding_repository.create_cve_reference(
        db_session,
        finding_id=finding.id,
        cve_id="CVE-2024-12345",
        cvss_score=None,
        cvss_vector=None,
        description=None,
        source_url=None,
    )

    assert reference.source_url is None
