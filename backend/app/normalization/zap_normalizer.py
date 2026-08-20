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

# `Finding.evidence` is an uncapped `Text` column DB-side, and a single ZAP
# alert can be reported at dozens/hundreds of URIs — joining every
# instance's evidence with no ceiling would let one alert produce a
# multi-hundred-KB string that then gets returned in every findings-list
# API response. Truncated at the normalizer, not the DB layer, since this
# is specifically about the join fan-out, not a general finding-size limit.
_MAX_EVIDENCE_LENGTH = 10_000


def _evidence_from_instances(alert: dict[str, Any]) -> str | None:
    # Each alert can occur at multiple URIs, each with its own `evidence`
    # string (the actual matched content, e.g. a response header or
    # snippet) under `instances[]`. `alert["solution"]` is remediation
    # advice, a different concept — it must not be used as evidence.
    # `FindingData` has one `evidence` field per alert (not per instance),
    # so every instance's evidence is joined into one string.
    parts = [
        instance["evidence"]
        for instance in (alert.get("instances") or [])
        if instance.get("evidence")
    ]
    if not parts:
        return None
    joined = "; ".join(parts)
    return joined[:_MAX_EVIDENCE_LENGTH]


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
                    evidence=_evidence_from_instances(alert),
                    confidence=alert.get("confidence"),
                )
            )
    return NormalizedData(findings=findings)
