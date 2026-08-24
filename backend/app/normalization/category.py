"""Coarse vulnerability-category classification, shared across normalizers.

Both ground-truth catalogs (scripts/ground_truth/*.json) use a small,
closed vocabulary for `vulnerability_type`: injection, xss,
security_misconfiguration, sensitive_data_exposure, vulnerable_component,
xxe. Before this module, every normalizer wrote its own flat,
one-size-fits-all `finding_type` (ZAP: "web_vulnerability" for every
alert, Nikto: "web_misconfiguration" for everything, Nuclei: the raw
protocol `type` like "http") that could never match that vocabulary —
not a fabricated bug, a structural gap `scripts/ground_truth/
match_findings.py`'s own docstring already documented for its tier-2
match ("finding_type is coarse... does little to disambiguate ZAP/Nikto
findings from each other").

Centralized here, not duplicated per normalizer, for the same reason
severity.py already is: one shared, testable mapping instead of three
copies that could silently drift apart.
"""

from typing import Any

# ZAP alerts carry a standard CWE id (https://cwe.mitre.org/). "0"/"-1"
# are ZAP's own sentinel values for "no CWE applies" (confirmed against a
# real scan's raw output). Only CWEs actually plausible from a DAST tool's
# alert set are mapped; anything else — known-but-unmapped, or genuinely
# unknown — falls back to security_misconfiguration (the closest
# "something's off, not necessarily exploitable on its own" bucket)
# rather than guessing at a more specific, possibly wrong category.
_ZAP_CWE_TO_CATEGORY: dict[str, str] = {
    "89": "injection",  # SQL Injection
    "78": "injection",  # OS Command Injection
    "77": "injection",  # Command Injection
    "79": "xss",  # Cross-Site Scripting
    "611": "xxe",  # XML External Entity
    "22": "security_misconfiguration",  # Path Traversal
    "200": "sensitive_data_exposure",  # Information Exposure
    "209": "sensitive_data_exposure",  # Info exposure through an error message
    "532": "sensitive_data_exposure",  # Info exposure through a log file
    "548": "sensitive_data_exposure",  # Info exposure through directory listing
    "497": "sensitive_data_exposure",  # Exposure of sensitive system info
    "319": "sensitive_data_exposure",  # Cleartext transmission
    "614": "security_misconfiguration",  # Cookie without Secure flag
    "1004": "security_misconfiguration",  # Cookie without HttpOnly
    "1021": "security_misconfiguration",  # Clickjacking (missing frame protection)
    "693": "security_misconfiguration",  # Protection mechanism failure
    "16": "security_misconfiguration",  # Configuration
    "829": "vulnerable_component",  # Inclusion of functionality from an untrusted source
    "937": "vulnerable_component",  # Using components with known vulnerabilities
}


def from_zap_cweid(cweid: str | int | None) -> str:
    if cweid is None:
        return "security_misconfiguration"
    return _ZAP_CWE_TO_CATEGORY.get(str(cweid), "security_misconfiguration")


# Nikto has no structured category field at all — only a free-text `msg`.
# Checked against real captured Nikto output
# (scripts/ground_truth/sample_run_dvwa_authenticated_findings.json):
# every one of those 15 real findings is a misconfiguration/
# info-disclosure message with no injection/xss wording at all, so in
# practice this heuristic rarely reclassifies anything away from
# security_misconfiguration — which matches Nikto's actual detection
# profile (it doesn't probe injection points the way Nuclei/ZAP do).
# Documented as a heuristic, not a guarantee: a text classifier over a
# tool's own free-text summary can misfire on unusual wording.
_INJECTION_KEYWORDS = ("sql injection", "sqli", "command injection", "os command")
_XSS_KEYWORDS = ("cross site scripting", "cross-site scripting", "xss")


def from_nikto_message(msg: str) -> str:
    lowered = msg.lower()
    if any(kw in lowered for kw in _INJECTION_KEYWORDS):
        return "injection"
    if any(kw in lowered for kw in _XSS_KEYWORDS):
        return "xss"
    return "security_misconfiguration"


# Nuclei templates carry a thematic `info.tags` list (e.g. ["sqli", "dvwa"]
# or ["xss"]) — unlike the raw `type` field (protocol-level: "http",
# "network", ...), tags follow the nuclei-templates project's own naming
# convention and are a real signal of vulnerability category.
_NUCLEI_TAG_TO_CATEGORY: dict[str, str] = {
    "sqli": "injection",
    "sql-injection": "injection",
    "rce": "injection",
    "command-injection": "injection",
    "xss": "xss",
    "xxe": "xxe",
    "exposure": "sensitive_data_exposure",
    "disclosure": "sensitive_data_exposure",
    "misconfig": "security_misconfiguration",
    "default-login": "security_misconfiguration",
    "cve": "vulnerable_component",
    "outdated-version": "vulnerable_component",
}


def from_nuclei_tags(tags: Any) -> str:
    if isinstance(tags, str):
        tags = tags.split(",")
    if not isinstance(tags, list):
        return "security_misconfiguration"
    for tag in tags:
        category = _NUCLEI_TAG_TO_CATEGORY.get(str(tag).strip().lower())
        if category:
            return category
    return "security_misconfiguration"
