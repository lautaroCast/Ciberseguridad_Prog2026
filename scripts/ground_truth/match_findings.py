"""Match pipeline findings against a ground-truth catalog and compute
recall, precision, F1, false-positive rate per tool, and inter-tool
overlap.

Design notes (read before trusting a number this script prints):

Matching is inherently approximate, because tool output is heterogeneous
free text, not a structured claim tied to a catalog id. Three tiers, in
priority order, each with a different confidence level — reported
separately, never blended into one number:

  1. CVE match (exact string equality between a finding's CVE references
     and a catalog entry's `cve`). Highest confidence. Only Nuclei findings
     in this pipeline ever carry a CVE (see backend/app/normalization/
     nuclei_normalizer.py), and neither ground-truth catalog currently has
     any CVE-backed entries (Juice Shop challenges are app-specific, DVWA
     entries are unauthenticated-blocked before any CVE-bearing surface is
     reached) — so this tier is expected to produce zero matches against
     the current catalogs. Kept as tier 1 anyway so the script does the
     right thing if a CVE-bearing catalog entry is ever added.
  2. finding_type + location overlap: the finding's `finding_type`
     equals the catalog entry's `vulnerability_type`, AND the finding's
     evidence/URL text overlaps the catalog entry's `location.path`
     (substring match, tolerant of trailing slashes/query strings).
     Medium confidence. `finding_type` is now a real, shared coarse
     category (injection/xss/security_misconfiguration/
     sensitive_data_exposure/vulnerable_component/xxe — see
     backend/app/normalization/category.py) derived per tool (ZAP's CWE
     id, Nikto's message text, Nuclei's template tags) instead of one
     flat string per tool — until that existed, this tier could
     essentially never fire for ZAP/Nikto findings no matter how correct
     they were.
  3. Keyword fallback: case-insensitive substring match of any of the
     catalog entry's `description_keywords` against the finding's
     title/evidence text. Lowest confidence, explicitly flagged as a
     "weak match" in the output — can produce false positives (a finding
     coincidentally containing a keyword) and false negatives (a real
     detection phrased differently than the catalog's wording). Any
     recall/precision number that leans heavily on tier-3 matches should
     be treated as indicative, not authoritative — this script always
     reports the match-tier breakdown so that's visible, never hidden in
     a single blended percentage. Candidate (entry, finding) pairs are
     collected across the *whole* remaining catalog first and assigned by
     specificity (most keyword hits wins, ties broken by the shorter
     keyword list) rather than "whichever catalog entry is processed
     first claims the first finding it hits" — two entries sharing an
     overly generic word (e.g. "injection" appearing in more than one
     DVWA entry's keyword list) used to let file order decide the wrong
     winner.

Unmatched findings and uncovered catalog entries are both listed in the
output for manual review — not just discarded — since the auditor's own
standard for this kind of analysis is that unverifiable claims must be
flagged, not asserted.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_HERE = Path(__file__).parent


@dataclass
class MatchResult:
    catalog_entry_id: str
    finding_id: str
    tool: str
    tier: str  # "cve" | "type_location" | "keyword"


@dataclass
class MatchReport:
    target: str
    total_findings: int
    total_catalog_entries: int
    matches: list[MatchResult] = field(default_factory=list)
    unmatched_finding_ids: list[str] = field(default_factory=list)
    uncovered_catalog_entry_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "total_findings": self.total_findings,
            "total_catalog_entries": self.total_catalog_entries,
            "matches": [m.__dict__ for m in self.matches],
            "unmatched_finding_ids": self.unmatched_finding_ids,
            "uncovered_catalog_entry_ids": self.uncovered_catalog_entry_ids,
            # "metrics_by_tool" is filled in by build_report(), which needs
            # per-tool finding *totals* (not just matches) that this class
            # doesn't have on its own — left out of dict form here on purpose.
            "match_tier_breakdown": tier_breakdown(self),
            "inter_tool_overlap": inter_tool_overlap(self),
        }


def _normalize_path(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[?#].*$", "", text.strip().lower()).rstrip("/")


def _location_overlaps(finding_evidence: str | None, catalog_path: str | None) -> bool:
    if not catalog_path:
        return False
    ev = _normalize_path(finding_evidence)
    cp = _normalize_path(catalog_path)
    if not ev or not cp:
        return False
    # Pad both with "/" boundaries so a plain substring check can't match
    # across unrelated paths that merely share a prefix (e.g. catalog "/api"
    # must not match evidence "/api-docs/...").
    padded_ev = f"/{ev.strip('/')}/"
    padded_cp = f"/{cp.strip('/')}/"
    return padded_cp in padded_ev


def _keyword_hit_count(finding: dict, keywords: list[str]) -> int:
    # `.get(key, "")` only substitutes the default when the key is
    # missing, not when its value is None (e.g. a finding with no
    # evidence still has an "evidence": null key from the API) — `or ""`
    # catches both, so a None field can't turn into the literal
    # substring "none" in the haystack and spuriously match a keyword.
    title = finding.get("title") or ""
    evidence = finding.get("evidence") or ""
    description = finding.get("description") or ""
    haystack = f"{title} {evidence} {description}".lower()
    return sum(1 for kw in keywords if kw in haystack)


def match(
    findings: list[dict],
    tool_by_scan_task_id: dict[str, str],
    catalog: list[dict],
    target_label: str,
) -> MatchReport:
    report = MatchReport(
        target=target_label,
        total_findings=len(findings),
        total_catalog_entries=len(catalog),
    )
    matched_finding_ids: set[str] = set()
    matched_catalog_ids: set[str] = set()

    finding_cves: dict[str, set[str]] = {
        f["id"]: {c["cve_id"] for c in f.get("cve_references", [])} for f in findings
    }

    for entry in catalog:
        entry_id = entry["id"]

        # Tier 1: CVE
        if entry.get("cve"):
            for f in findings:
                if f["id"] in matched_finding_ids:
                    continue
                if entry["cve"] in finding_cves.get(f["id"], set()):
                    report.matches.append(
                        MatchResult(
                            entry_id, f["id"], tool_by_scan_task_id.get(f["scan_task_id"], "?"),
                            "cve",
                        )
                    )
                    matched_finding_ids.add(f["id"])
                    matched_catalog_ids.add(entry_id)

        # Tier 2: finding_type + location
        if entry_id not in matched_catalog_ids:
            for f in findings:
                if f["id"] in matched_finding_ids:
                    continue
                if f.get("finding_type") == entry.get("vulnerability_type") and _location_overlaps(
                    f.get("evidence"), (entry.get("location") or {}).get("path")
                ):
                    report.matches.append(
                        MatchResult(
                            entry_id, f["id"], tool_by_scan_task_id.get(f["scan_task_id"], "?"),
                            "type_location",
                        )
                    )
                    matched_finding_ids.add(f["id"])
                    matched_catalog_ids.add(entry_id)

    # Tier 3: keyword fallback. Unlike tiers 1-2 (exact CVE equality,
    # type+location overlap — both precise enough that processing order
    # can't create a wrong assignment), a plain "first catalog entry
    # processed wins any single keyword hit" is order-dependent and
    # genuinely wrong: two entries sharing a too-generic keyword (e.g.
    # both DVWA-exec's ["command","injection"] and DVWA-sqli's
    # ["injection"] contain "injection") let whichever happens to come
    # first in the catalog file steal a finding from the entry that
    # actually deserves it. Collect every (entry, finding) candidate pair
    # first, then assign globally by specificity: most keyword hits wins,
    # ties broken by the entry with the shorter (more specific) keyword
    # list — closer to "best match" than "first match".
    candidates: list[tuple[int, int, str, str]] = []
    for entry in catalog:
        entry_id = entry["id"]
        if entry_id in matched_catalog_ids:
            continue
        keywords = entry.get("description_keywords") or []
        if not keywords:
            continue
        for f in findings:
            if f["id"] in matched_finding_ids:
                continue
            hits = _keyword_hit_count(f, keywords)
            if hits > 0:
                candidates.append((hits, len(keywords), entry_id, f["id"]))

    candidates.sort(key=lambda c: (-c[0], c[1]))
    findings_by_id = {f["id"]: f for f in findings}
    for _hits, _keyword_count, entry_id, finding_id in candidates:
        if entry_id in matched_catalog_ids or finding_id in matched_finding_ids:
            continue
        f = findings_by_id[finding_id]
        report.matches.append(
            MatchResult(entry_id, finding_id, tool_by_scan_task_id.get(f["scan_task_id"], "?"), "keyword")
        )
        matched_finding_ids.add(finding_id)
        matched_catalog_ids.add(entry_id)

    report.unmatched_finding_ids = [f["id"] for f in findings if f["id"] not in matched_finding_ids]
    report.uncovered_catalog_entry_ids = [
        e["id"] for e in catalog if e["id"] not in matched_catalog_ids
    ]
    return report


def tier_breakdown(report: MatchReport) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for m in report.matches:
        counts[m.tier] += 1
    return dict(counts)


def inter_tool_overlap(report: MatchReport) -> dict[str, Any]:
    tools_by_entry: dict[str, set[str]] = defaultdict(set)
    for m in report.matches:
        tools_by_entry[m.catalog_entry_id].add(m.tool)
    multi_tool_entries = {k: sorted(v) for k, v in tools_by_entry.items() if len(v) > 1}
    total_matched_entries = len(tools_by_entry)
    return {
        "catalog_entries_matched_by_multiple_tools": multi_tool_entries,
        "count": len(multi_tool_entries),
        "pct_of_matched_entries": (
            round(100 * len(multi_tool_entries) / total_matched_entries, 1)
            if total_matched_entries
            else 0.0
        ),
    }


def build_report(
    findings: list[dict], scan_tasks: list[dict], catalog: list[dict], target_label: str
) -> dict[str, Any]:
    tool_by_scan_task_id = {t["id"]: t["tool_name"] for t in scan_tasks}
    report = match(findings, tool_by_scan_task_id, catalog, target_label)
    result = report.to_dict()

    findings_by_tool: dict[str, int] = defaultdict(int)
    for f in findings:
        findings_by_tool[tool_by_scan_task_id.get(f["scan_task_id"], "?")] += 1

    matched_findings_by_tool: dict[str, int] = defaultdict(int)
    for m in report.matches:
        matched_findings_by_tool[m.tool] += 1

    catalog_by_tool_class: dict[str, int] = defaultdict(int)
    entries_matched_at_least_once_by_tool: dict[str, set[str]] = defaultdict(set)
    for m in report.matches:
        entries_matched_at_least_once_by_tool[m.tool].add(m.catalog_entry_id)

    metrics: dict[str, dict[str, float | int]] = {}
    all_tools = set(findings_by_tool) | set(matched_findings_by_tool)
    for tool in sorted(all_tools):
        total = findings_by_tool.get(tool, 0)
        tp = matched_findings_by_tool.get(tool, 0)
        fp = total - tp
        recall_denominator = len(catalog)  # catalog entries applicable to this target overall
        recall_numerator = len(entries_matched_at_least_once_by_tool.get(tool, set()))
        precision = round(tp / total, 3) if total else None
        recall = round(recall_numerator / recall_denominator, 3) if recall_denominator else None
        if precision is None or recall is None:
            f1 = None
        elif precision + recall == 0:
            f1 = 0.0
        else:
            f1 = round(2 * precision * recall / (precision + recall), 3)
        fpr = round(fp / total, 3) if total else None
        metrics[tool] = {
            "total_findings": total,
            "true_positive_findings": tp,
            "false_positive_findings": fp,
            "catalog_entries_matched": recall_numerator,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "false_positive_rate": fpr,
        }

    result["metrics_by_tool"] = metrics
    return result


def load_catalog(*paths: Path) -> list[dict]:
    entries: list[dict] = []
    for p in paths:
        entries.extend(json.loads(p.read_text(encoding="utf-8")))
    return entries


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--findings-json", type=Path, required=True)
    parser.add_argument("--scan-tasks-json", type=Path, required=True)
    parser.add_argument("--catalog-json", type=Path, nargs="+", required=True)
    parser.add_argument("--target-label", type=str, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    findings = json.loads(args.findings_json.read_text(encoding="utf-8"))
    scan_tasks = json.loads(args.scan_tasks_json.read_text(encoding="utf-8"))
    catalog = load_catalog(*args.catalog_json)

    report = build_report(findings, scan_tasks, catalog, args.target_label)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote match report to {args.output}")
    print(json.dumps(report["metrics_by_tool"], indent=2))
