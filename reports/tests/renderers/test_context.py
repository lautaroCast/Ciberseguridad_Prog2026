from app.renderers.context import build_context
from app.schemas.report import ReportRequest, ScanInfo, TargetInfo


def test_findings_sorted_worst_first(sample_report_request):
    context = build_context(sample_report_request)
    severities = [f.severity for f in context["findings"]]
    assert severities == ["critical", "medium", "low", "info"]


def test_severity_counts(sample_report_request):
    context = build_context(sample_report_request)
    assert context["severity_counts"] == {
        "critical": 1,
        "medium": 1,
        "low": 1,
        "info": 1,
    }


def test_target_and_scan_pass_through(sample_report_request):
    context = build_context(sample_report_request)
    assert context["target"] is sample_report_request.target
    assert context["scan"] is sample_report_request.scan


def test_generated_at_present(sample_report_request):
    context = build_context(sample_report_request)
    assert context["generated_at"] is not None


def test_empty_findings():
    request = ReportRequest(
        format="json",
        target=TargetInfo(id="t", name="n", host="h"),
        scan=ScanInfo(id="s", status="completed"),
        findings=[],
    )
    context = build_context(request)
    assert context["findings"] == []
    assert context["severity_counts"] == {}
