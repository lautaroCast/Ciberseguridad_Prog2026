import os

os.environ.setdefault("INTERNAL_API_KEY", "test-internal-api-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.schemas.report import (  # noqa: E402
    CveReferenceInfo,
    FindingInfo,
    ReportRequest,
    ScanInfo,
    TargetInfo,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, headers={"X-Internal-Token": os.environ["INTERNAL_API_KEY"]})


@pytest.fixture
def sample_report_request() -> ReportRequest:
    return ReportRequest(
        format="json",
        target=TargetInfo(id="target-1", name="juice-shop-demo", host="juice-shop"),
        scan=ScanInfo(id="scan-1", status="completed", triggered_by="n8n-pipeline"),
        findings=[
            FindingInfo(
                id="finding-1",
                title="DVWA Default Login",
                finding_type="http",
                severity="critical",
                created_at="2026-07-18T22:09:40.833311Z",
                cve_references=[
                    CveReferenceInfo(cve_id="CVE-2021-1234", cvss_score="9.1"),
                ],
            ),
            FindingInfo(
                id="finding-2",
                title="Content Security Policy (CSP) Header Not Set",
                finding_type="web_vulnerability",
                severity="medium",
                created_at="2026-07-18T22:09:40.833311Z",
            ),
            FindingInfo(
                id="finding-3",
                title="Timestamp Disclosure - Unix",
                finding_type="web_vulnerability",
                severity="low",
                created_at="2026-07-18T22:09:40.833311Z",
            ),
            FindingInfo(
                id="finding-4",
                title="Modern Web Application",
                finding_type="web_vulnerability",
                severity="info",
                created_at="2026-07-18T22:09:40.833311Z",
            ),
        ],
    )


@pytest.fixture
def xss_report_request(sample_report_request: ReportRequest) -> ReportRequest:
    data = sample_report_request.model_dump()
    data["findings"][0]["title"] = "<script>alert(1)</script>"
    return ReportRequest(**data)


@pytest.fixture
def scan_error_report_request(sample_report_request: ReportRequest) -> ReportRequest:
    """7th independent evaluation: a scan that completed but had a tool
    failure along the way (ScanInfo.error_message set) — used to confirm
    the warning renders in every format, not just that the field parses."""
    data = sample_report_request.model_dump()
    data["scan"]["error_message"] = "nuclei: tool exited with code 1, no results collected"
    return ReportRequest(**data)


@pytest.fixture
def confidence_cvss_report_request(sample_report_request: ReportRequest) -> ReportRequest:
    """9th independent evaluation: confidence/cvss_score are normalized onto
    every finding (zap_normalizer.py, nuclei_normalizer.py) but were never
    rendered in HTML/Markdown — only JSON, as a side effect of dumping the
    whole model. No cve_references here, to isolate that this is the
    finding's own confidence/cvss_score, not a CVE's."""
    data = sample_report_request.model_dump()
    data["findings"][1]["confidence"] = "3"
    data["findings"][1]["cvss_score"] = "6.1"
    data["findings"][1]["cvss_vector"] = "CVSS:3.1/AV:N/AC:L"
    return ReportRequest(**data)
