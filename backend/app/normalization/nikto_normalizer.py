"""Nikto -> `findings` rows.

Nikto's `-Format json` output is a **list** of per-host scan reports
(confirmed by hand while building this module — one entry per host nikto
was pointed at, even for a single-target scan), each holding a flat
`vulnerabilities` list. No CVSS score or severity label is attached
anywhere in the output, so every finding here is conservatively set to
LOW — an analyst using the dashboard should treat these as "worth
reviewing", not as pre-triaged by risk the way Nuclei/ZAP findings are
(both of which carry a tool-native severity).
"""

from typing import Any

from app.normalization.types import FindingData, NormalizedData
from models import SeverityLevel


def normalize(parsed: list[dict[str, Any]] | None) -> NormalizedData:
    findings = [
        FindingData(
            title=str(item.get("msg") or "Nikto finding")[:255],
            finding_type="web_misconfiguration",
            severity=SeverityLevel.LOW,
            evidence=f"{item.get('method', 'GET')} {item.get('url', '')}".strip(),
            confidence="low",
        )
        for host_report in (parsed or [])
        for item in (host_report.get("vulnerabilities") or [])
    ]
    return NormalizedData(findings=findings)
