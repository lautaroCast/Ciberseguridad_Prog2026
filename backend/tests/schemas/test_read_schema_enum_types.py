"""Regression: ScanRead.status, FindingRead.severity, ReportRead.format and
ScanTaskRead.status used to be typed as plain `str` instead of their real
enum, so the OpenAPI schema documented them as an unconstrained string and
Pydantic never validated a response value against the actual vocabulary.
Wire format is unaffected (these enums are `str` subclasses — JSON
serialization already produced the same value either way), so this only
asserts the field's declared type, not any behavior change."""

from app.schemas.finding import FindingRead
from app.schemas.report import ReportRead
from app.schemas.scan import ScanRead
from app.schemas.scan_task import ScanTaskRead
from models import ReportFormat, ScanStatus, ScanTaskStatus, SeverityLevel


def test_scan_read_status_is_the_real_enum():
    assert ScanRead.model_fields["status"].annotation is ScanStatus


def test_finding_read_severity_is_the_real_enum():
    assert FindingRead.model_fields["severity"].annotation is SeverityLevel


def test_report_read_format_is_the_real_enum():
    assert ReportRead.model_fields["format"].annotation is ReportFormat


def test_scan_task_read_status_is_the_real_enum():
    assert ScanTaskRead.model_fields["status"].annotation is ScanTaskStatus
