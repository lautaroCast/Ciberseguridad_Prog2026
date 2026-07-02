"""CVSS-score and tool-native-label mapping to `SeverityLevel`.

One shared module so every normalizer classifies severity through the
same rules instead of each tool inventing its own thresholds. CVSS v3
qualitative ranges follow FIRST.org's spec: None=0.0, Low=0.1-3.9,
Medium=4.0-6.9, High=7.0-8.9, Critical=9.0-10.0.
"""

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
