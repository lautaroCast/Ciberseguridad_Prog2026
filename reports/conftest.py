import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.report import CveReferenceInfo, FindingInfo, ReportRequest, ScanInfo, TargetInfo


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


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
