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
