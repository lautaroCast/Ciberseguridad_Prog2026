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
