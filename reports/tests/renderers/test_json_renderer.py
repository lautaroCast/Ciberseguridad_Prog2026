import json

from app.renderers.json_renderer import render_json


def test_renders_valid_json(sample_report_request):
    output = render_json(sample_report_request)
    parsed = json.loads(output)
    assert set(parsed.keys()) == {"target", "scan", "severity_counts", "findings", "generated_at"}


def test_findings_and_counts_reflected(sample_report_request):
    parsed = json.loads(render_json(sample_report_request))
    assert len(parsed["findings"]) == 4
    assert parsed["severity_counts"]["critical"] == 1
    assert parsed["target"]["host"] == "juice-shop"


def test_cve_references_included(sample_report_request):
    parsed = json.loads(render_json(sample_report_request))
    critical_finding = next(f for f in parsed["findings"] if f["severity"] == "critical")
    assert critical_finding["cve_references"][0]["cve_id"] == "CVE-2021-1234"
