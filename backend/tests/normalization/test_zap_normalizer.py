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
    # Both instances contribute: the second has no evidence text, but its
    # uri is kept (5th independent evaluation - ground-truth location
    # matching needs real URL data, which used to be discarded entirely).
    assert result.findings[0].evidence == (
        "http://juice-shop/: no csp header on /; http://juice-shop/login"
    )
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
    assert result.findings[0].evidence == (
        "http://juice-shop/a: Set-Cookie: a=1; http://juice-shop/b: Set-Cookie: b=2"
    )


def test_evidence_is_none_when_no_instances():
    parsed = {"site": [{"alerts": [{"name": "X", "riskcode": "3"}]}]}
    result = zap_normalizer.normalize(parsed)
    assert result.findings[0].evidence is None


def test_finding_type_derived_from_cweid_not_flat_string():
    # 5th independent evaluation: finding_type used to be
    # "web_vulnerability" for every single alert, so it could never match
    # a ground-truth catalog's vulnerability_type (injection/xss/...).
    parsed = {"site": [{"alerts": [{"name": "SQL Injection", "riskcode": "3", "cweid": "89"}]}]}
    result = zap_normalizer.normalize(parsed)
    assert result.findings[0].finding_type == "injection"


def test_finding_type_falls_back_when_cweid_is_zap_sentinel():
    parsed = {"site": [{"alerts": [{"name": "Modern Web Application", "riskcode": "0", "cweid": "-1"}]}]}
    result = zap_normalizer.normalize(parsed)
    assert result.findings[0].finding_type == "security_misconfiguration"


def test_evidence_is_truncated_for_alerts_with_many_instances():
    # Code-review regression: an alert reported at many URIs used to join
    # evidence with no size ceiling, unlike the caps added elsewhere in
    # the same remediation (raw_output/error_message).
    instances = [{"uri": f"http://juice-shop/{i}", "evidence": "x" * 100} for i in range(200)]
    parsed = {"site": [{"alerts": [{"name": "X", "riskcode": "1", "instances": instances}]}]}
    result = zap_normalizer.normalize(parsed)
    assert len(result.findings[0].evidence) == zap_normalizer._MAX_EVIDENCE_LENGTH
