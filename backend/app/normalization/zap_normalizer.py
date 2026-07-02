"""OWASP ZAP -> `findings` rows.

ZAP's quick-scan report groups alerts under `site[].alerts[]`; each alert
carries a `riskcode` ("0".."3") which is a more reliable severity signal
than parsing its human-readable `riskdesc` string (e.g. "High (Medium)").
ZAP alerts reference CWEs, not CVEs, so no `CveReferenceData` is produced
here.
"""

from typing import Any

from app.normalization import severity
from app.normalization.types import FindingData, NormalizedData


def normalize(parsed: dict[str, Any] | None) -> NormalizedData:
    if not parsed:
        return NormalizedData()
    findings: list[FindingData] = []
    for site in parsed.get("site") or []:
        for alert in site.get("alerts") or []:
            findings.append(
                FindingData(
                    title=str(alert.get("name") or "ZAP finding")[:255],
                    finding_type="web_vulnerability",
                    severity=severity.from_zap_riskcode(alert.get("riskcode")),
                    description=alert.get("desc"),
                    evidence=alert.get("solution"),
                    confidence=alert.get("confidence"),
                )
            )
    return NormalizedData(findings=findings)
