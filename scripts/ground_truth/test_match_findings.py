"""Tests for match_findings.py — no DB/service dependencies, pure functions.

Run inside the backend container (has pytest + is where scripts/ is
baked in): `docker compose exec backend pytest scripts/ground_truth/test_match_findings.py`
"""

from match_findings import build_report, match


def _finding(id_, *, finding_type=None, evidence=None, title=None, description=None,
             scan_task_id="t1", cve_references=None):
    return {
        "id": id_,
        "scan_task_id": scan_task_id,
        "finding_type": finding_type,
        "evidence": evidence,
        "title": title or "",
        "description": description,
        "cve_references": cve_references or [],
    }


def _entry(id_, *, vulnerability_type=None, path=None, keywords=None, cve=None):
    return {
        "id": id_,
        "vulnerability_type": vulnerability_type,
        "location": {"path": path} if path else {},
        "description_keywords": keywords or [],
        "cve": cve,
    }


def test_tier1_cve_match():
    findings = [_finding("f1", cve_references=[{"cve_id": "CVE-2024-1"}])]
    catalog = [_entry("e1", cve="CVE-2024-1")]
    report = match(findings, {"t1": "nuclei"}, catalog, "test")
    assert len(report.matches) == 1
    assert report.matches[0].tier == "cve"


def test_tier2_type_and_location_match():
    findings = [_finding("f1", finding_type="injection", evidence="http://dvwa/vulnerabilities/sqli/")]
    catalog = [_entry("e1", vulnerability_type="injection", path="/vulnerabilities/sqli/")]
    report = match(findings, {"t1": "zap"}, catalog, "test")
    assert len(report.matches) == 1
    assert report.matches[0].tier == "type_location"


def test_tier2_requires_both_type_and_location():
    # Same type, different location - must not match.
    findings = [_finding("f1", finding_type="injection", evidence="http://dvwa/vulnerabilities/exec/")]
    catalog = [_entry("e1", vulnerability_type="injection", path="/vulnerabilities/sqli/")]
    report = match(findings, {"t1": "zap"}, catalog, "test")
    assert report.matches == []


def test_tier3_keyword_specificity_beats_file_order():
    # Regression: DVWA-exec (processed first, keywords include the overly
    # generic "injection") used to steal a finding that DVWA-sqli (more
    # specific in real usage, though here it's the *only* keyword) should
    # have matched instead. A finding whose text hits 2 keywords must be
    # assigned to the entry with more keyword hits, not to whichever
    # entry is listed first in the catalog.
    findings = [_finding("f1", title="SQL Injection found")]
    catalog = [
        _entry("DVWA-exec", keywords=["command", "injection"]),  # 1 hit ("injection")
        _entry("DVWA-sqli", keywords=["sql", "injection"]),  # 2 hits ("sql", "injection")
    ]
    report = match(findings, {"t1": "zap"}, catalog, "test")
    assert len(report.matches) == 1
    assert report.matches[0].catalog_entry_id == "DVWA-sqli"


def test_tier3_tie_broken_by_shorter_keyword_list():
    findings = [_finding("f1", title="injection detected")]
    catalog = [
        _entry("broad", keywords=["injection", "generic", "extra"]),  # 1 hit, 3 keywords
        _entry("specific", keywords=["injection"]),  # 1 hit, 1 keyword
    ]
    report = match(findings, {"t1": "zap"}, catalog, "test")
    assert len(report.matches) == 1
    assert report.matches[0].catalog_entry_id == "specific"


def test_tier3_empty_keywords_never_matches():
    findings = [_finding("f1", title="anything at all")]
    catalog = [_entry("e1", keywords=[])]
    report = match(findings, {"t1": "zap"}, catalog, "test")
    assert report.matches == []
    assert report.uncovered_catalog_entry_ids == ["e1"]


def test_a_finding_matches_at_most_one_entry_and_vice_versa():
    findings = [_finding("f1", title="sql injection"), _finding("f2", title="sql injection")]
    catalog = [_entry("e1", keywords=["sql", "injection"])]
    report = match(findings, {"t1": "zap"}, catalog, "test")
    # Only one finding can claim the one catalog entry, even though both
    # findings independently hit the same keywords.
    assert len(report.matches) == 1
    assert len(report.unmatched_finding_ids) == 1


def test_build_report_computes_recall_precision_per_tool():
    findings = [
        _finding("f1", scan_task_id="t-zap", title="sql injection"),
        _finding("f2", scan_task_id="t-zap", title="unrelated finding"),
    ]
    tasks = [{"id": "t-zap", "tool_name": "zap"}]
    catalog = [_entry("e1", keywords=["sql", "injection"])]
    result = build_report(findings, tasks, catalog, "test")
    metrics = result["metrics_by_tool"]["zap"]
    assert metrics["total_findings"] == 2
    assert metrics["true_positive_findings"] == 1
    assert metrics["catalog_entries_matched"] == 1
    assert metrics["recall"] == 1.0
    assert metrics["precision"] == 0.5
