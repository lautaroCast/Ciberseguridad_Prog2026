"""Renders a `ReportRequest` to an HTML string via Jinja2.

`autoescape=True` is deliberate, not the Jinja default-off behavior:
finding titles/descriptions come straight from scan tool output (Nikto,
Nuclei, ZAP...), and a finding literally titled `<script>alert(1)</script>`
(a real, plausible XSS-detector result) must not be reflected unescaped
into the report — that would be a self-inflicted XSS in the report viewer.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.renderers.context import build_context
from app.schemas.report import ReportRequest

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(enabled_extensions=(), default=True),
)


def render_html(data: ReportRequest) -> str:
    template = _env.get_template("report.html.jinja2")
    return template.render(**build_context(data))
