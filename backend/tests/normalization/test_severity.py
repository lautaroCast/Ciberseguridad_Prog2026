import pytest

from app.normalization import severity
from models import SeverityLevel


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (None, SeverityLevel.INFO),
        (0, SeverityLevel.INFO),
        (0.1, SeverityLevel.LOW),
        (3.9, SeverityLevel.LOW),
        (4.0, SeverityLevel.MEDIUM),
        (6.9, SeverityLevel.MEDIUM),
        (7.0, SeverityLevel.HIGH),
        (8.9, SeverityLevel.HIGH),
        (9.0, SeverityLevel.CRITICAL),
        (10.0, SeverityLevel.CRITICAL),
    ],
)
def test_from_cvss_score_boundaries(score, expected):
    assert severity.from_cvss_score(score) == expected


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("info", SeverityLevel.INFO),
        ("informational", SeverityLevel.INFO),
        ("unknown", SeverityLevel.INFO),
        ("low", SeverityLevel.LOW),
        ("Low", SeverityLevel.LOW),
        ("  Low  ", SeverityLevel.LOW),
        ("medium", SeverityLevel.MEDIUM),
        ("high", SeverityLevel.HIGH),
        ("critical", SeverityLevel.CRITICAL),
        ("CRITICAL", SeverityLevel.CRITICAL),
        ("something-else", SeverityLevel.INFO),
        (None, SeverityLevel.INFO),
        ("", SeverityLevel.INFO),
    ],
)
def test_from_label(label, expected):
    assert severity.from_label(label) == expected


@pytest.mark.parametrize(
    ("riskcode", "expected"),
    [
        ("0", SeverityLevel.INFO),
        ("1", SeverityLevel.LOW),
        ("2", SeverityLevel.MEDIUM),
        ("3", SeverityLevel.HIGH),
        (0, SeverityLevel.INFO),
        (2, SeverityLevel.MEDIUM),
        ("4", SeverityLevel.INFO),
        (None, SeverityLevel.INFO),
    ],
)
def test_from_zap_riskcode(riskcode, expected):
    assert severity.from_zap_riskcode(riskcode) == expected
