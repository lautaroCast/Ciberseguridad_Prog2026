"""OWASP ZAP -> `findings` rows.

ZAP's quick-scan report groups alerts under `site[].alerts[]`; each alert
carries a `riskcode` ("0".."3") which is a more reliable severity signal
than parsing its human-readable `riskdesc` string (e.g. "High (Medium)").
ZAP alerts reference CWEs, not CVEs, so no `CveReferenceData` is produced
here.
"""

from typing import Any

from app.normalization import category, severity
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
    #
    # The URI is prefixed onto its own instance's evidence (not just the
    # evidence text alone, and kept even when an instance has no evidence
    # text) so that ground-truth location matching
    # (scripts/ground_truth/match_findings.py's tier 2) has real URL data
    # to compare against — it used to be discarded entirely, so a ZAP
    # finding could never match a catalog entry by location no matter how
    # correct the finding was.
    parts = []
    for instance in alert.get("instances") or []:
        uri = instance.get("uri")
        evidence = instance.get("evidence")
        if uri and evidence:
            parts.append(f"{uri}: {evidence}")
        elif uri:
            parts.append(uri)
        elif evidence:
            parts.append(evidence)
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
                    title=str(alert.get("name") or "ZAP finding"),
                    finding_type=category.from_zap_cweid(alert.get("cweid")),
                    severity=severity.from_zap_riskcode(alert.get("riskcode")),
                    description=alert.get("desc"),
                    evidence=_evidence_from_instances(alert),
                    confidence=alert.get("confidence"),
                )
            )
    return NormalizedData(findings=findings)
