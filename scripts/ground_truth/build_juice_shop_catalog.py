"""Build juice_shop_catalog.json from Juice Shop's own official challenge list.

Source: juice_shop_challenges_raw.yml, vendored verbatim from
/juice-shop/data/static/challenges.yml inside the running `juice-shop`
container (bundled with the app, not something we authored) — this is the
project's own documented vulnerability catalog, per the audit's own
recommendation (C-09) to build ground truth "from Juice Shop's and DVWA's
own public vulnerability catalogs."

Not every challenge is a scanner-detectable vulnerability: many are
business-logic/game challenges (e.g. "put 3 different products in your
basket and manipulate the request... so that you end up paying less than
0 for it") with no CVE, no CVSS meaning, and no network-observable
signature a DAST/network scanner could plausibly flag. Filtering those
out is a judgment call, made here at the *category* level (not by
cherry-picking individual challenges) so the inclusion policy is
reproducible and auditable rather than silently baked into a hand-curated
list:

INCLUDED categories — plausibly detectable by Nmap/WhatWeb/Nikto/Nuclei/
ZAP without needing multi-step business-logic exploitation:
  - XSS                    (ZAP active scan, Nuclei XSS templates)
  - Injection               (ZAP active scan: SQLi/NoSQLi/command injection)
  - Vulnerable Components   (Nuclei CVE templates, WhatWeb fingerprinting)
  - Security Misconfiguration (Nikto, ZAP passive scan, Nuclei misconfig templates)
  - XXE                     (ZAP active scan)
  - Sensitive Data Exposure (Nikto/ZAP: only the subset that manifests as
                              a directly fetchable exposed resource, e.g.
                              an accessible backup/log/config file — NOT
                              the subset that requires chaining an
                              unrelated exploit first to reach the data)

EXCLUDED categories — require business-logic exploitation, multi-step
state manipulation, or client-side-only interaction that these five
tools' scan modes do not perform:
  Broken Access Control (mostly IDOR via guessed/sequential IDs reached
    only after authenticating as a specific role), Broken Authentication
    (mostly credential-stuffing/reset-flow abuse), Improper Input
    Validation (mostly checkout/business-rule bypasses, not a payload a
    scanner would craft), Cryptographic Issues (mostly "decode this
    encoded value you already have"), Miscellaneous, Observability
    Failures (mostly log-file discovery that overlaps with Sensitive Data
    Exposure but is largely path-guessing outside a scanner's default
    wordlist), Broken Anti Automation, Security through Obscurity,
    Insecure Deserialization (needs a crafted payload against a known
    endpoint, not something these tools' generic scan modes attempt),
    Unvalidated Redirects (needs a pre-known open-redirect parameter).

This is a coverage *ceiling* for the ground-truth set, not a claim that
excluded categories aren't real vulnerabilities — it only says the five
tools in this pipeline, run in their current unauthenticated/non-crawled-
business-logic modes, have no realistic path to detect them. Recall
computed against this filtered set therefore measures "recall against
scanner-reachable vulnerabilities," not "recall against every challenge
in Juice Shop" — this distinction must be carried into any recall number
quoted in the thesis text (see docs/audit-corrections/).

Difficulty is not used as a filter: a difficulty-6 challenge in an
included category still gets a catalog entry (with a note if it clearly
also requires app-specific interaction ZAP's spider won't trigger, e.g.
challenges gated by prior login) so the ground truth doesn't inflate
apparent recall by omitting hard-but-technically-detectable entries.

Rerun after any Juice Shop image upgrade: re-extract
juice_shop_challenges_raw.yml (see this repo's docs/audit-corrections/
for the exact `docker exec` command used) and re-run this script, since
the upstream challenge list does change between releases.
"""

import json
import re
from pathlib import Path

import yaml

_HERE = Path(__file__).parent
_RAW_YAML = _HERE / "juice_shop_challenges_raw.yml"
_OUTPUT = _HERE / "juice_shop_catalog.json"

INCLUDED_CATEGORIES = {
    "XSS": "xss",
    "Injection": "injection",
    "Vulnerable Components": "vulnerable_component",
    "Security Misconfiguration": "security_misconfiguration",
    "XXE": "xxe",
    "Sensitive Data Exposure": "sensitive_data_exposure",
}

# Sensitive Data Exposure challenges that need a prior unrelated exploit
# (not a directly fetchable resource) — excluded even though the category
# is generally included. Keyed by the challenge's stable `key` field.
_SENSITIVE_DATA_EXPOSURE_EXCLUDE_KEYS = {
    "passwordHashLeakChallenge",  # needs an authenticated session first
    "userCredentialsChallenge",   # needs a JWT/session already obtained elsewhere
}


def _detectable_by_tool_class(category: str) -> list[str]:
    if category == "XXE":
        return ["dast"]
    if category in ("Injection", "XSS"):
        return ["dast", "template_scanner"]
    if category == "Vulnerable Components":
        return ["template_scanner", "fingerprinter"]
    if category == "Security Misconfiguration":
        return ["dast", "misconfig_scanner", "fingerprinter"]
    if category == "Sensitive Data Exposure":
        return ["misconfig_scanner", "dast"]
    return []


def build() -> list[dict]:
    raw = yaml.safe_load(_RAW_YAML.read_text(encoding="utf-8"))
    entries = []
    for challenge in raw:
        category = challenge.get("category")
        if category not in INCLUDED_CATEGORIES:
            continue
        key = challenge.get("key")
        if category == "Sensitive Data Exposure" and key in _SENSITIVE_DATA_EXPOSURE_EXCLUDE_KEYS:
            continue

        entries.append(
            {
                "id": f"JS-{key}",
                "source": "Juice Shop official challenges.yml (bundled in the running "
                "juice-shop image), category-filtered per this script's own docstring",
                "vulnerability_type": INCLUDED_CATEGORIES[category],
                "juice_shop_category": category,
                "cve": None,  # Juice Shop challenges are app-specific, not CVE-backed
                "location": {"path": None, "port": 3000},
                "description_keywords": _keywords(challenge),
                "expected_severity": _expected_severity(challenge.get("difficulty", 3)),
                "detectable_by_tool_class": _detectable_by_tool_class(category),
                "difficulty": challenge.get("difficulty"),
                "name": challenge.get("name"),
            }
        )
    return entries


# 5th independent evaluation: keywords used to come only from the
# challenge's display `name` — Juice Shop's own flavor/narrative text
# (e.g. "User Credentials" for a SQL injection challenge, "NFT Takeover"
# for a wallet-exposure one), often disconnected from the actual
# vulnerability class. "User Credentials" -> ["credentials", "user"]
# caused a real false match against an unrelated ZAP finding titled "User
# Agent Fuzzer", purely because both strings contain "user".
#
# Every entry is now seeded with terms tied to its own vulnerability_type
# (a fact this script already knows, not a guess) so it always has at
# least one keyword consistent with what it actually is, even when
# Juice Shop's own text gives no technical hint at all (e.g.
# xxeDosChallenge's description is literally "Give the server something
# to chew on for quite a while" — no XXE-related word anywhere).
_CATEGORY_SEED_KEYWORDS: dict[str, list[str]] = {
    "XSS": ["xss", "scripting"],
    "Injection": ["injection", "sql", "nosql"],
    "Vulnerable Components": ["vulnerable", "outdated", "component"],
    "Security Misconfiguration": ["misconfiguration", "exposed", "default"],
    "XXE": ["xxe", "entity", "xml"],
    "Sensitive Data Exposure": ["exposure", "disclosure", "leak", "sensitive"],
}

# First attempt at this fix also folded in every >3-char word from the
# challenge's full-sentence `description` unconditionally — descriptions
# are prose, not short labels like `name`, so that pulled in ordinary
# function words ("with", "your", "which", "another", "could", "final",
# "luckily", ...) as "keywords", causing exactly the kind of coincidental
# false match (Nikto's generic "Suggested security header missing"
# matching unrelated XSS/injection challenges) this whole fix exists to
# prevent. Filtered here instead of trusting `len() > 3` alone to mean
# "technical term".
_STOPWORDS = {
    "about", "after", "again", "against", "along", "also", "always", "another",
    "arent", "around", "before", "being", "belong", "between", "both", "cant",
    "come", "could", "dangit", "danger", "despite", "didnt", "doesnt", "dont",
    "down", "during", "each", "either", "even", "every", "final", "first",
    "from", "have", "here", "however", "important", "inform", "into",
    "isnt", "itself", "just", "know", "least", "less", "like", "luckily",
    "made", "make", "many", "might", "more", "most", "much", "must", "never",
    "note", "nothing", "once", "one", "onto", "original", "other", "otherwise",
    "over", "quite", "read", "really", "saying", "shall", "should", "since",
    "some", "something", "still", "such", "sure", "take", "than", "that",
    "their", "them", "then", "there", "these", "they", "this", "those",
    "through", "trick", "under", "until", "very", "wasnt", "well", "were",
    "what", "when", "where", "which", "while", "will", "with", "within",
    "without", "wont", "would", "your", "yours", "yourself",
}

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_ENTITY_OR_TAG_FRAGMENT_RE = re.compile(r"[<>&]|&[a-z]+;")


def _description_terms(description: str) -> set[str]:
    text = _HTML_TAG_RE.sub(" ", description or "")
    words = {w.strip(".,()`\"'").lower() for w in text.split() if len(w) > 3}
    return {
        w
        for w in words
        if w not in _STOPWORDS and not _ENTITY_OR_TAG_FRAGMENT_RE.search(w)
    }


def _keywords(challenge: dict) -> list[str]:
    seed = set(_CATEGORY_SEED_KEYWORDS.get(challenge.get("category", ""), []))
    name_words = {
        w.strip(".,()").lower() for w in challenge.get("name", "").split() if len(w) > 3
    }
    keywords = seed | name_words
    # Description text only contributes when name+seed alone would leave
    # this entry with fewer than 2 keywords (e.g. xxeDosChallenge, whose
    # name "XXE DoS" already gives "xxe"/"dos" but "dos" is 3 chars and
    # gets filtered) — the common case (a name like "Reflected XSS")
    # already has enough real signal without pulling in prose noise too.
    if len(keywords) < 2:
        keywords |= _description_terms(challenge.get("description") or "")
    return sorted(keywords)


def _expected_severity(difficulty: int) -> str:
    # Juice Shop's difficulty (1-6, exploitation effort) is not a severity
    # scale — this is a rough, explicitly-approximate mapping so the
    # catalog has *some* expected_severity for reporting, not a claim that
    # difficulty equals impact.
    if difficulty <= 1:
        return "low"
    if difficulty <= 3:
        return "medium"
    if difficulty <= 5:
        return "high"
    return "critical"


if __name__ == "__main__":
    entries = build()
    _OUTPUT.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(entries)} catalog entries to {_OUTPUT}")
