from app.renderers.html_renderer import render_html


def test_renders_html_with_expected_content(sample_report_request):
    output = render_html(sample_report_request)
    assert "<!DOCTYPE html>" in output
    assert "juice-shop-demo" in output
    assert "DVWA Default Login" in output


def test_xss_title_is_escaped(xss_report_request):
    output = render_html(xss_report_request)
    assert "<script>alert(1)</script>" not in output
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in output


def test_scan_error_message_renders_as_warning(scan_error_report_request):
    output = render_html(scan_error_report_request)
    assert "nuclei: tool exited with code 1, no results collected" in output
    assert "Advertencia" in output


def test_no_warning_block_when_scan_has_no_error(sample_report_request):
    output = render_html(sample_report_request)
    assert "Advertencia" not in output


def test_finding_confidence_and_cvss_score_render(confidence_cvss_report_request):
    output = render_html(confidence_cvss_report_request)
    assert "Confianza: 3" in output
    assert "CVSS 6.1" in output
    assert "CVSS:3.1/AV:N/AC:L" in output


def test_no_confidence_or_cvss_line_when_absent(sample_report_request):
    output = render_html(sample_report_request)
    assert "Confianza:" not in output
