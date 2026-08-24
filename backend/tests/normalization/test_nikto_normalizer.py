from app.normalization import nikto_normalizer
from models import SeverityLevel


def test_flattens_hosts_and_vulnerabilities():
    parsed = [
        {
            "vulnerabilities": [
                {"msg": "This might be interesting.", "method": "GET", "url": "/ftp/"},
                {"msg": "Contains authorization information.", "url": "/.htpasswd"},
            ]
        },
        {"vulnerabilities": [{"msg": "Another host's finding"}]},
    ]
    result = nikto_normalizer.normalize(parsed)
    assert len(result.findings) == 3
    assert result.findings[0].title == "This might be interesting."
    assert result.findings[0].evidence == "GET /ftp/"
    assert result.findings[1].evidence == "GET /.htpasswd"  # method defaults to GET


def test_always_low_severity_regardless_of_content():
    # Nikto's own output carries no CVSS/severity signal at all — this
    # normalizer conservatively always classifies LOW, unlike nuclei/zap.
    parsed = [{"vulnerabilities": [{"msg": "anything"}]}]
    result = nikto_normalizer.normalize(parsed)
    assert result.findings[0].severity == SeverityLevel.LOW


def test_finding_type_classified_from_message_text():
    # 5th independent evaluation: finding_type used to be
    # "web_misconfiguration" for every single finding, unconditionally.
    parsed = [{"vulnerabilities": [{"msg": "SQL Injection possible via id parameter"}]}]
    result = nikto_normalizer.normalize(parsed)
    assert result.findings[0].finding_type == "injection"


def test_missing_vulnerabilities_key():
    parsed = [{}]
    result = nikto_normalizer.normalize(parsed)
    assert result.findings == []


def test_empty_input():
    assert nikto_normalizer.normalize([]).findings == []
    assert nikto_normalizer.normalize(None).findings == []
