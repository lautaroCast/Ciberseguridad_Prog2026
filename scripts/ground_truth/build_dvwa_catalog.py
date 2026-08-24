"""Build dvwa_catalog.json from DVWA's own module structure.

Source: the actual `vulnerabilities/` directory inside the running `dvwa`
container (`vulnerables/web-dvwa:latest`), listed directly —
`docker exec vulnscan-dvwa ls /var/www/html/vulnerabilities/` — not from
memory or a secondary source. This is DVWA's own documented set of
vulnerability categories, per the audit's recommendation (C-09) to build
ground truth from the targets' own catalogs. Directory → display-name
mapping below matches DVWA's own navigation menu labels (unchanged across
DVWA releases for this well-known image).

INCLUDED modules — plausibly reachable by an active DAST scan
(Nmap/WhatWeb/Nikto/Nuclei/ZAP) *if authentication were not a barrier*:
  csp, csrf, exec, fi, sqli, sqli_blind, upload, weak_id, xss_d, xss_r, xss_s

EXCLUDED modules — need multi-step credential/business-logic interaction
these tools' scan modes don't attempt: brute (Brute Force login — needs a
wordlist attack against a specific form), captcha (Insecure CAPTCHA —
needs solving/bypassing a CAPTCHA flow), javascript (client-side JS
puzzle, not a network-observable vulnerability signature).

*** CRITICAL, VERIFIED CAVEAT — READ BEFORE QUOTING ANY RECALL NUMBER ***
Every module page above lives behind DVWA's login wall. Confirmed
empirically in this session: an unauthenticated request to
`/vulnerabilities/sqli/` returns `302 Found` → `Location: ../../login.php`
(see `docker exec vulnscan-scanner curl -sD - http://dvwa/vulnerabilities/sqli/`
in this session's history) — with a `Set-Cookie: security=low` on the same
response, confirming DVWA's default security level is the easiest one, but
that's irrelevant if the page is never reached at all. The platform's own
pipeline runs Nmap/WhatWeb/Nikto/Nuclei/ZAP *unauthenticated* (see
docs/security.md's limitations and thesis §14.2's own admission of this).
This means every entry in this catalog is currently unreachable by the
platform as deployed — `reachable_unauthenticated` is `false` for all of
them. Recall computed against this catalog under the current pipeline
should be expected to be ~0% for DVWA, not because the tools are weak, but
because the target's own login wall blocks them before they ever see a
vulnerable page. This is a real, load-bearing finding for the measurement
campaign and the thesis's limitations chapter — it must be reported as
such, not smoothed over. (An authenticated scan mode, or a
pre-authentication step added to the pipeline before invoking the web
tools, would be the fix — out of scope for this correction pass, but
worth flagging as a concrete "trabajo futuro" item distinct from the
already-declared authenticated-scanning line of work.)
"""

import json
from pathlib import Path

_HERE = Path(__file__).parent
_OUTPUT = _HERE / "dvwa_catalog.json"

# (module_dir, display_name, vulnerability_type, expected_severity, detectable_by_tool_class)
_INCLUDED_MODULES = [
    ("csp", "Content Security Policy Bypass", "security_misconfiguration", "medium", ["dast"]),
    ("csrf", "Cross Site Request Forgery (CSRF)", "security_misconfiguration", "medium", ["dast"]),
    ("exec", "Command Injection", "injection", "critical", ["dast"]),
    ("fi", "File Inclusion", "injection", "high", ["dast"]),
    ("sqli", "SQL Injection", "injection", "critical", ["dast"]),
    ("sqli_blind", "SQL Injection (Blind)", "injection", "critical", ["dast"]),
    ("upload", "File Upload", "security_misconfiguration", "critical", ["dast"]),
    ("weak_id", "Weak Session IDs", "security_misconfiguration", "medium", ["dast"]),
    ("xss_d", "Cross Site Scripting (DOM)", "xss", "medium", ["dast"]),
    ("xss_r", "Cross Site Scripting (Reflected)", "xss", "medium", ["dast", "template_scanner"]),
    ("xss_s", "Cross Site Scripting (Stored)", "xss", "high", ["dast", "template_scanner"]),
]


def build() -> list[dict]:
    entries = []
    for module_dir, name, vuln_type, severity, tool_classes in _INCLUDED_MODULES:
        entries.append(
            {
                "id": f"DVWA-{module_dir}",
                "source": "DVWA's own vulnerabilities/ directory structure "
                "(vulnerables/web-dvwa:latest, verified via `docker exec vulnscan-dvwa ls "
                "/var/www/html/vulnerabilities/` in this session)",
                "vulnerability_type": vuln_type,
                "dvwa_module": name,
                "cve": None,
                "location": {"path": f"/vulnerabilities/{module_dir}/", "port": 80},
                # 5th independent evaluation: `len(w) > 3` silently dropped
                # "SQL" (3 chars) from "SQL Injection"'s own name, leaving
                # DVWA-sqli with the single, overly generic keyword
                # ["injection"] - shared with DVWA-exec/DVWA-fi/
                # DVWA-sqli_blind, making it collision-prone by
                # construction. `>= 3` keeps genuine short technical
                # acronyms (SQL, DOM, ...) without pulling in filler words
                # (all of which are 1-2 chars: "a", "of", "in", ...).
                "description_keywords": sorted(
                    {w.strip("()").lower() for w in name.split() if len(w) >= 3}
                ),
                "expected_severity": severity,
                "detectable_by_tool_class": tool_classes,
                # See this file's module docstring: verified empirically this
                # session that every /vulnerabilities/* path 302-redirects an
                # unauthenticated client to login.php. None of these are
                # actually reachable by the current unauthenticated pipeline.
                "reachable_unauthenticated": False,
            }
        )
    return entries


if __name__ == "__main__":
    entries = build()
    _OUTPUT.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(entries)} catalog entries to {_OUTPUT}")
