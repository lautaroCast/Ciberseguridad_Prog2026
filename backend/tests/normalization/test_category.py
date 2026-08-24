from app.normalization import category


def test_zap_cweid_maps_known_categories():
    assert category.from_zap_cweid("89") == "injection"
    assert category.from_zap_cweid("79") == "xss"
    assert category.from_zap_cweid("611") == "xxe"
    assert category.from_zap_cweid("548") == "sensitive_data_exposure"


def test_zap_cweid_falls_back_for_unknown_or_missing():
    assert category.from_zap_cweid("0") == "security_misconfiguration"
    assert category.from_zap_cweid("-1") == "security_misconfiguration"
    assert category.from_zap_cweid(None) == "security_misconfiguration"
    assert category.from_zap_cweid("999999") == "security_misconfiguration"


def test_nikto_message_detects_injection_and_xss_keywords():
    assert category.from_nikto_message("SQL Injection possible in parameter x") == "injection"
    assert category.from_nikto_message("Cross Site Scripting (XSS) vector") == "xss"


def test_nikto_message_falls_back_for_generic_misconfiguration_text():
    # Matches every one of the 15 real Nikto findings captured in
    # scripts/ground_truth/sample_run_dvwa_authenticated_findings.json.
    assert category.from_nikto_message("Apache default file found.") == "security_misconfiguration"
    assert category.from_nikto_message("Directory indexing found.") == "security_misconfiguration"


def test_nuclei_tags_maps_known_categories():
    assert category.from_nuclei_tags(["sqli", "dvwa"]) == "injection"
    assert category.from_nuclei_tags(["xss"]) == "xss"
    assert category.from_nuclei_tags("cve,outdated-version") == "vulnerable_component"


def test_nuclei_tags_falls_back_for_unmapped_or_missing():
    assert category.from_nuclei_tags(["some-unmapped-tag"]) == "security_misconfiguration"
    assert category.from_nuclei_tags(None) == "security_misconfiguration"
    assert category.from_nuclei_tags([]) == "security_misconfiguration"
