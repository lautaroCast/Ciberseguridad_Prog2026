"""Renders a `ReportRequest` to a Markdown string via Jinja2.

Uses its own `autoescape=False` environment, unlike `html_renderer`:
Markdown is plain text, not HTML, so HTML-escaping finding titles here
would corrupt the output (e.g. a literal `&lt;script&gt;` showing up in a
.md file instead of `<script>`) rather than protect against anything —
there's no browser interpreting this output as markup.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.renderers.context import build_context
from app.schemas.report import ReportRequest

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), autoescape=False)  # noqa: S701 — plain text output, not HTML


def render_markdown(data: ReportRequest) -> str:
    template = _env.get_template("report.md.jinja2")
    return template.render(**build_context(data))
