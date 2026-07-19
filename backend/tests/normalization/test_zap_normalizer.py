from app.normalization import zap_normalizer
from models import SeverityLevel


def test_walks_nested_sites_and_alerts():
    parsed = {
        "site": [
            {
                "alerts": [
                    {"name": "CSP Header Not Set", "riskcode": "2", "desc": "..."},
                    {"name": "Cookie No HttpOnly Flag", "riskcode": "1"},
                ]
            },
            {"alerts": [{"name": "Directory Browsing", "riskcode": "2"}]},
        ]
    }
    result = zap_normalizer.normalize(parsed)
    assert len(result.findings) == 3
    assert result.findings[0].severity == SeverityLevel.MEDIUM
    assert result.findings[1].severity == SeverityLevel.LOW


def test_no_cve_references_produced():
    parsed = {"site": [{"alerts": [{"name": "X", "riskcode": "3"}]}]}
    result = zap_normalizer.normalize(parsed)
    assert result.findings[0].cve_references == []


def test_empty_site_list():
    assert zap_normalizer.normalize({"site": []}).findings == []


def test_falsy_input_returns_empty():
    assert zap_normalizer.normalize(None).findings == []
    assert zap_normalizer.normalize({}).findings == []
