from app.renderers.markdown_renderer import render_markdown


def test_renders_non_empty_markdown(sample_report_request):
    output = render_markdown(sample_report_request)
    assert isinstance(output, str)
    assert output.strip()


def test_contains_target_and_findings(sample_report_request):
    output = render_markdown(sample_report_request)
    assert "juice-shop-demo" in output
    assert "DVWA Default Login" in output
    assert "CRITICAL" in output


def test_severity_summary_table_present(sample_report_request):
    output = render_markdown(sample_report_request)
    assert "| CRITICAL | 1 |" in output
    assert "| INFO | 1 |" in output


def test_scan_error_message_renders_as_warning(scan_error_report_request):
    output = render_markdown(scan_error_report_request)
    assert "nuclei: tool exited with code 1, no results collected" in output
    assert "Advertencia" in output


def test_no_warning_block_when_scan_has_no_error(sample_report_request):
    output = render_markdown(sample_report_request)
    assert "Advertencia" not in output
