"""Dispatches a `ReportRequest` to the right renderer and writes the file.

The only place `format` is switched on — routers and renderers don't need
to know about each other. Adding a new export format is: one renderer
function returning str/bytes, one branch here, no changes anywhere else
(same plugin-ish shape as the Scanner Service's adapter registry and the
Backend's normalization registry, minus a dict since there are only four
formats and they're unlikely to grow into a real plugin list).
"""

from datetime import UTC, datetime
from pathlib import Path

from app.renderers.html_renderer import render_html
from app.renderers.json_renderer import render_json
from app.renderers.markdown_renderer import render_markdown
from app.renderers.pdf_renderer import render_pdf
from app.schemas.report import ReportRequest, ReportResult

_EXTENSIONS = {"pdf": "pdf", "html": "html", "markdown": "md", "json": "json"}


def generate(data: ReportRequest, output_dir: Path) -> ReportResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{data.scan.id}.{_EXTENSIONS[data.format]}"
    path = output_dir / filename

    if data.format == "pdf":
        path.write_bytes(render_pdf(data))
    elif data.format == "html":
        path.write_text(render_html(data), encoding="utf-8")
    elif data.format == "markdown":
        path.write_text(render_markdown(data), encoding="utf-8")
    else:
        path.write_text(render_json(data), encoding="utf-8")

    return ReportResult(format=data.format, filename=filename, generated_at=datetime.now(UTC))
