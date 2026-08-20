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


def test_evidence_comes_from_instances_not_solution():
    # COD-4 regression: `solution` is remediation advice, not evidence —
    # it must never end up in `evidence`, even when present.
    parsed = {
        "site": [
            {
                "alerts": [
                    {
                        "name": "CSP Header Not Set",
                        "riskcode": "2",
                        "solution": "Ensure that your web server sets a CSP header.",
                        "instances": [
                            {"uri": "http://juice-shop/", "evidence": "no csp header on /"},
                            {"uri": "http://juice-shop/login", "evidence": ""},
                        ],
                    }
                ]
            }
        ]
    }
    result = zap_normalizer.normalize(parsed)
    assert result.findings[0].evidence == "no csp header on /"
    assert "Ensure that" not in (result.findings[0].evidence or "")


def test_evidence_joins_multiple_instances():
    parsed = {
        "site": [
            {
                "alerts": [
                    {
                        "name": "Cookie No HttpOnly Flag",
                        "riskcode": "1",
                        "instances": [
                            {"uri": "http://juice-shop/a", "evidence": "Set-Cookie: a=1"},
                            {"uri": "http://juice-shop/b", "evidence": "Set-Cookie: b=2"},
                        ],
                    }
                ]
            }
        ]
    }
    result = zap_normalizer.normalize(parsed)
    assert result.findings[0].evidence == "Set-Cookie: a=1; Set-Cookie: b=2"


def test_evidence_is_none_when_no_instances():
    parsed = {"site": [{"alerts": [{"name": "X", "riskcode": "3"}]}]}
    result = zap_normalizer.normalize(parsed)
    assert result.findings[0].evidence is None


def test_evidence_is_truncated_for_alerts_with_many_instances():
    # Code-review regression: an alert reported at many URIs used to join
    # evidence with no size ceiling, unlike the caps added elsewhere in
    # the same remediation (raw_output/error_message).
    instances = [{"uri": f"http://juice-shop/{i}", "evidence": "x" * 100} for i in range(200)]
    parsed = {"site": [{"alerts": [{"name": "X", "riskcode": "1", "instances": instances}]}]}
    result = zap_normalizer.normalize(parsed)
    assert len(result.findings[0].evidence) == zap_normalizer._MAX_EVIDENCE_LENGTH
