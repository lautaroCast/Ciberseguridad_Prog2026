"""Nuclei -> `findings` rows (+ CVE references when a template maps to one).

Each JSONL line already carries a tool-native severity
(`info`/`low`/`medium`/`high`/`critical`) and, for CVE-backed templates,
`info.classification.cve-id` / `cvss-score` — the most structured input
any tool in this service produces, so this is the only normalizer that
trusts the tool's own severity label instead of deriving one.
"""

from typing import Any

from app.normalization import severity
from app.normalization.types import CveReferenceData, FindingData, NormalizedData


def normalize(parsed: list[dict[str, Any]] | None) -> NormalizedData:
    findings: list[FindingData] = []
    for item in parsed or []:
        info = item.get("info") or {}
        classification = info.get("classification") or {}
        cve_ids = classification.get("cve-id") or []
        cvss_score = classification.get("cvss-score")
        cve_references = [
            CveReferenceData(cve_id=str(cve_id), cvss_score=cvss_score) for cve_id in cve_ids
        ]
        findings.append(
            FindingData(
                title=str(info.get("name") or item.get("template-id") or "Nuclei finding")[:255],
                finding_type=str(item.get("type") or "template_match"),
                severity=severity.from_label(info.get("severity")),
                description=info.get("description"),
                evidence=item.get("matched-at") or item.get("host"),
                cvss_score=cvss_score,
                cvss_vector=classification.get("cvss-metrics"),
                cve_references=cve_references,
            )
        )
    return NormalizedData(findings=findings)
