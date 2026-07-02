"""Converts a rendered HTML report to PDF bytes via WeasyPrint.

Reuses `html_renderer.render_html` rather than maintaining a separate PDF
template — the HTML report's `@page`/print-oriented CSS (see
`templates/report.html.jinja2`) is written to render correctly both in a
browser and as a PDF, so there is exactly one template to keep in sync.
"""

from weasyprint import HTML

from app.renderers.html_renderer import render_html
from app.schemas.report import ReportRequest


def render_pdf(data: ReportRequest) -> bytes:
    html = render_html(data)
    return HTML(string=html).write_pdf()
