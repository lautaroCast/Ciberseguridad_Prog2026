"""Nuclei -> `findings` rows (+ CVE references when a template maps to one).

Each JSONL line already carries a tool-native severity
(`info`/`low`/`medium`/`high`/`critical`) and, for CVE-backed templates,
`info.classification.cve-id` / `cvss-score` — the most structured input
any tool in this service produces, so this is the only normalizer that
trusts the tool's own severity label instead of deriving one.
"""

from typing import Any

from app.normalization import category, severity
from app.normalization.types import CveReferenceData, FindingData, NormalizedData


def normalize(parsed: list[dict[str, Any]] | None) -> NormalizedData:
    findings: list[FindingData] = []
    for item in parsed or []:
        info = item.get("info") or {}
        classification = info.get("classification") or {}
        cve_ids = classification.get("cve-id") or []
        # A bare string here (instead of the list real Nuclei output always
        # uses) would otherwise iterate per character below, producing one
        # bogus single-character CveReferenceData per character instead of
        # one real reference — same defensive shape category.from_nuclei_tags
        # already uses for its own possibly-bare-string field.
        if isinstance(cve_ids, str):
            cve_ids = [cve_ids]
        cvss_score = classification.get("cvss-score")
        cve_references = [
            CveReferenceData(cve_id=str(cve_id), cvss_score=cvss_score) for cve_id in cve_ids
        ]
        # Trust the tool's own label when present (see module docstring) —
        # only fall back to the shared CVSS-score mapping when Nuclei
        # didn't provide one at all, so a template that omits `severity`
        # doesn't silently land in INFO despite a real, high CVSS score.
        raw_severity = info.get("severity")
        severity_value = (
            severity.from_label(raw_severity)
            if raw_severity
            else severity.from_cvss_score(cvss_score)
        )
        findings.append(
            FindingData(
                title=str(info.get("name") or item.get("template-id") or "Nuclei finding"),
                # `item["type"]` is the protocol Nuclei used (http/dns/...),
                # not a vulnerability category — `info.tags` (5th
                # independent evaluation) is the real thematic signal.
                finding_type=category.from_nuclei_tags(info.get("tags")),
                severity=severity_value,
                description=info.get("description"),
                evidence=item.get("matched-at") or item.get("host"),
                cvss_score=cvss_score,
                cvss_vector=classification.get("cvss-metrics"),
                cve_references=cve_references,
            )
        )
    return NormalizedData(findings=findings)
