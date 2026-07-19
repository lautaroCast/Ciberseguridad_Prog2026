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
