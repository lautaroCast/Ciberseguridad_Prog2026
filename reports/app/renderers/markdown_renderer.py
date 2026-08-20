"""Renders a `ReportRequest` to a Markdown string via Jinja2.

Uses its own `autoescape=False` environment, unlike `html_renderer`:
Markdown is plain text, not HTML, so HTML-escaping finding titles here
would corrupt the output (e.g. a literal `&lt;script&gt;` showing up in a
.md file instead of `<script>`) rather than protect against anything —
there's no browser interpreting this output as markup.

WARNING: this is only safe as long as nothing downstream ever converts
this .md output back into HTML. Finding titles/descriptions/evidence come
directly from scan tool output run against a target designed to be
vulnerable — a title like `<img src=x onerror=alert(1)>` is stored
unescaped here. Most Markdown-to-HTML renderers (the `markdown` package,
marked.js, many static-site generators) pass raw inline HTML through by
default unless explicitly sanitized, which would turn that into a live
stored-XSS payload. There is currently no such downstream renderer in
this project, so this is a latent risk, not an active vulnerability — but
if one is ever added, it must sanitize/escape this output before
rendering it as HTML.
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
