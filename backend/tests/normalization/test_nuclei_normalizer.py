from app.normalization import nuclei_normalizer
from models import SeverityLevel


def test_cve_references_extracted():
    parsed = [
        {
            "template-id": "dvwa-default-login",
            "type": "http",
            "matched-at": "http://dvwa:80/index.php",
            "info": {
                "name": "DVWA Default Login",
                "severity": "critical",
                "classification": {"cve-id": ["CVE-2021-1234"], "cvss-score": 9.1},
            },
        }
    ]
    result = nuclei_normalizer.normalize(parsed)
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.title == "DVWA Default Login"
    assert finding.severity == SeverityLevel.CRITICAL
    assert finding.cve_references[0].cve_id == "CVE-2021-1234"
    assert finding.cve_references[0].cvss_score == 9.1


def test_cve_id_as_bare_string_is_treated_as_one_reference_not_iterated_per_character():
    # 6th independent evaluation: cve-id was assumed to always be a list -
    # a bare string would otherwise iterate per character, producing one
    # bogus single-character CveReferenceData per character.
    parsed = [
        {
            "template-id": "some-template",
            "info": {
                "name": "Bare-string CVE",
                "severity": "high",
                "classification": {"cve-id": "CVE-2021-1234", "cvss-score": 7.5},
            },
        }
    ]
    result = nuclei_normalizer.normalize(parsed)
    assert len(result.findings[0].cve_references) == 1
    assert result.findings[0].cve_references[0].cve_id == "CVE-2021-1234"


def test_missing_classification_yields_no_cve_references():
    parsed = [{"info": {"name": "Some finding", "severity": "info"}}]
    result = nuclei_normalizer.normalize(parsed)
    assert result.findings[0].cve_references == []


def test_falls_back_to_template_id_when_no_name():
    parsed = [{"template-id": "generic-tech-detect", "info": {}}]
    result = nuclei_normalizer.normalize(parsed)
    assert result.findings[0].title == "generic-tech-detect"


def test_empty_input():
    assert nuclei_normalizer.normalize([]).findings == []
    assert nuclei_normalizer.normalize(None).findings == []


def test_finding_type_derived_from_tags_not_protocol_type():
    # 5th independent evaluation: finding_type used to be item["type"]
    # (the protocol Nuclei used, e.g. "http") - never a real vulnerability
    # category, so it could never match a ground-truth catalog entry.
    parsed = [
        {
            "type": "http",
            "template-id": "dvwa-sqli",
            "info": {"name": "SQLi", "severity": "high", "tags": ["sqli", "dvwa"]},
        }
    ]
    result = nuclei_normalizer.normalize(parsed)
    assert result.findings[0].finding_type == "injection"


def test_falls_back_to_cvss_score_when_tool_severity_label_is_missing():
    # Some community templates omit info.severity entirely. Without a
    # fallback this used to be silently filed as INFO regardless of how
    # high the CVSS score actually is.
    parsed = [
        {
            "template-id": "some-template",
            "info": {
                "name": "High-severity finding with no tool label",
                "classification": {"cvss-score": 9.8},
            },
        }
    ]
    result = nuclei_normalizer.normalize(parsed)
    assert result.findings[0].severity == SeverityLevel.CRITICAL


def test_does_not_override_an_explicit_info_label_with_cvss_score():
    # The tool's own label is trusted when present, even if it's "info" and
    # a CVSS score is also attached — only a *missing* label falls back.
    parsed = [
        {
            "template-id": "some-template",
            "info": {
                "severity": "info",
                "classification": {"cvss-score": 9.8},
            },
        }
    ]
    result = nuclei_normalizer.normalize(parsed)
    assert result.findings[0].severity == SeverityLevel.INFO


def test_malformed_cvss_score_does_not_raise_and_falls_back_to_info():
    # 7th independent evaluation: a non-numeric cvss-score used to reach
    # severity.from_cvss_score's bare float() call unguarded, raising
    # ValueError partway through normalization - which the ingest
    # savepoint would roll back entirely, discarding every other real
    # finding from the same tool run.
    parsed = [
        {
            "template-id": "some-template",
            "info": {
                "name": "Malformed score finding",
                "classification": {"cvss-score": "not-a-number"},
            },
        }
    ]
    result = nuclei_normalizer.normalize(parsed)
    assert result.findings[0].severity == SeverityLevel.INFO
    assert result.findings[0].cvss_score is None


def test_out_of_range_cvss_score_is_clamped_not_stored_raw():
    parsed = [
        {
            "template-id": "some-template",
            "info": {
                "name": "Out-of-range score finding",
                "severity": "critical",
                "classification": {"cvss-score": 15.0},
            },
        }
    ]
    result = nuclei_normalizer.normalize(parsed)
    assert result.findings[0].cvss_score == 10.0
