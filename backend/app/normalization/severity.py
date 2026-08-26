"""CVSS-score and tool-native-label mapping to `SeverityLevel`.

One shared module so every normalizer classifies severity through the
same rules instead of each tool inventing its own thresholds. CVSS v3
qualitative ranges follow FIRST.org's spec: None=0.0, Low=0.1-3.9,
Medium=4.0-6.9, High=7.0-8.9, Critical=9.0-10.0.
"""

from typing import Any

from models import SeverityLevel

_LABELS: dict[str, SeverityLevel] = {
    "info": SeverityLevel.INFO,
    "informational": SeverityLevel.INFO,
    "unknown": SeverityLevel.INFO,
    "low": SeverityLevel.LOW,
    "medium": SeverityLevel.MEDIUM,
    "high": SeverityLevel.HIGH,
    "critical": SeverityLevel.CRITICAL,
}

_ZAP_RISKCODE: dict[str, SeverityLevel] = {
    "0": SeverityLevel.INFO,
    "1": SeverityLevel.LOW,
    "2": SeverityLevel.MEDIUM,
    "3": SeverityLevel.HIGH,
}


def sanitize_cvss_score(value: Any) -> float | None:
    """Coerces a tool-derived CVSS score to a real float in [0.0, 10.0],
    or None if it isn't usable at all.

    7th independent evaluation: nuclei_normalizer.py used to pass Nuclei's
    `classification["cvss-score"]` straight through, untouched, to both
    `from_cvss_score` below (a bare `float(score)`, no try/except) and to
    `Finding.cvss_score` (`Numeric(3,1)` — real cap 99.9). An unsanitized
    community Nuclei template with a non-numeric or out-of-range value
    would raise partway through normalization, and the single
    `db.begin_nested()` savepoint in scan_task_service.py rolls back the
    *entire* scan_task's findings, not just the bad one — silently
    zeroing out every real finding that tool run produced. Sanitizing
    once, here, before the value reaches either of those two call sites,
    closes the concrete trigger without changing that transaction's
    granularity (a per-finding savepoint would be a much larger, riskier
    change to fix a bad-input problem, not a transaction-design one).
    """
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(10.0, score))


def from_cvss_score(score: float | None) -> SeverityLevel:
    if score is None:
        return SeverityLevel.INFO
    value = float(score)
    if value <= 0:
        return SeverityLevel.INFO
    if value < 4.0:
        return SeverityLevel.LOW
    if value < 7.0:
        return SeverityLevel.MEDIUM
    if value < 9.0:
        return SeverityLevel.HIGH
    return SeverityLevel.CRITICAL


def from_label(label: str | None) -> SeverityLevel:
    if not label:
        return SeverityLevel.INFO
    return _LABELS.get(label.strip().lower(), SeverityLevel.INFO)


def from_zap_riskcode(riskcode: str | None) -> SeverityLevel:
    if riskcode is None:
        return SeverityLevel.INFO
    return _ZAP_RISKCODE.get(str(riskcode).strip(), SeverityLevel.INFO)
