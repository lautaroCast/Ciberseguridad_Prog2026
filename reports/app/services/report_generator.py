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

from app.paths import PathEscapesOutputDirError, atomic_write, resolve_within
from app.renderers.html_renderer import render_html
from app.renderers.json_renderer import render_json
from app.renderers.markdown_renderer import render_markdown
from app.renderers.pdf_renderer import render_pdf
from app.schemas.report import ReportRequest, ReportResult

_EXTENSIONS = {"pdf": "pdf", "html": "html", "markdown": "md", "json": "json"}


class InvalidReportRequestError(Exception):
    """Raised when `data.scan.id` would resolve to a path outside `output_dir`.

    `scan.id` is a bare `str` (no UUID/pattern constraint at the schema
    level) and flows directly into the output filename. In the documented
    flow it's always a Backend-generated UUID, but this service trusts the
    caller completely otherwise (see routers/reports.py's module
    docstring) — this is the only guard against a `"../../etc/x"`-style
    value, mirroring the one `download_report` already has.
    """


def generate(data: ReportRequest, output_dir: Path) -> ReportResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{data.scan.id}.{_EXTENSIONS[data.format]}"
    try:
        path = resolve_within(output_dir, filename)
    except PathEscapesOutputDirError as exc:
        raise InvalidReportRequestError(data.scan.id) from exc

    if data.format == "pdf":
        content = render_pdf(data)
    elif data.format == "html":
        content = render_html(data).encode("utf-8")
    elif data.format == "markdown":
        content = render_markdown(data).encode("utf-8")
    else:
        content = render_json(data).encode("utf-8")

    atomic_write(path, content)

    return ReportResult(format=data.format, filename=filename, generated_at=datetime.now(UTC))
