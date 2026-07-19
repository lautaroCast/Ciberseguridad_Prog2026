"""PDF rendering is deliberately deferred from this first test pass.

WeasyPrint needs native libraries (Pango/Cairo/GDK-Pixbuf, fontconfig) that
are only present inside the `reports` Docker image (see reports/Dockerfile),
not in an arbitrary host/CI environment. `pytest.importorskip` below means
this file quietly skips wherever those libs (and the `weasyprint` import
itself) aren't available, and only actually asserts anything when run
inside the real `reports` container (`docker compose exec reports pytest`).
"""

import pytest

weasyprint = pytest.importorskip("weasyprint")

from app.renderers.pdf_renderer import render_pdf  # noqa: E402


def test_renders_pdf_bytes(sample_report_request):
    output = render_pdf(sample_report_request)
    assert isinstance(output, bytes)
    assert output.startswith(b"%PDF-")
