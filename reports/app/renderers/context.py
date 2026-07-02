"""Shared template context: sorts findings by severity and counts them.

Every renderer (HTML, Markdown, JSON) needs the same derived view of a
`ReportRequest` — findings ranked worst-first, plus a per-severity count
for the summary section — so it's built once here instead of duplicated
per format.
"""

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from app.schemas.report import ReportRequest

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def build_context(data: ReportRequest) -> dict[str, Any]:
    findings_sorted = sorted(
        data.findings, key=lambda f: _SEVERITY_ORDER.get(f.severity, len(_SEVERITY_ORDER))
    )
    severity_counts = Counter(f.severity for f in data.findings)
    return {
        "target": data.target,
        "scan": data.scan,
        "findings": findings_sorted,
        "severity_counts": severity_counts,
        "generated_at": datetime.now(UTC),
    }
