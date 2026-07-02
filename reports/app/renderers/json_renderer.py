"""Renders a `ReportRequest` to a pretty-printed JSON string.

Not a template — the "rendering" here is just re-shaping the same
`build_context` data (findings sorted worst-first, plus per-severity
counts) that the HTML/Markdown renderers use, serialized directly. This
keeps the JSON export a structured, machine-readable superset of what the
human-readable formats show, rather than a raw dump of the request body.
"""

import json
from typing import Any

from app.renderers.context import build_context
from app.schemas.report import ReportRequest


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def render_json(data: ReportRequest) -> str:
    context = build_context(data)
    payload = {
        "target": _to_jsonable(context["target"]),
        "scan": _to_jsonable(context["scan"]),
        "severity_counts": dict(context["severity_counts"]),
        "findings": [_to_jsonable(f) for f in context["findings"]],
        "generated_at": context["generated_at"].isoformat(),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
