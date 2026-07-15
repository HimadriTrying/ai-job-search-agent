#!/usr/bin/env python3
"""
verify.py — the code-enforced honesty gate.

The single most important guarantee in this system: no outbound document may contain
an employer, title, credential, or hard metric that is not present in career_facts.yaml.

The AI reframes and reorders what is already true. This script proves it did not invent.
It is deliberately a *separate program* from the thing that writes the document — a prompt
that says "don't fabricate" is a promise; this is a check.

Usage:
    python honesty/verify.py <document.md|.txt|.tex>            # check one doc
    python honesty/verify.py --facts career_facts.yaml <doc>    # explicit facts path

Exit codes:
    0  = clean
    1  = potential fabrication found (fails loudly; the doc must be fixed, not the facts)
    2  = usage / file error

Design notes
------------
This is intentionally conservative: it FLAGS for human review rather than silently passing.
It catches the high-value cases (unknown org names, uncredentialed certs, orphan metrics).
It cannot catch every possible embellishment — pair it with the fresh-context Reviewer
subagent, which reads for framing and tone. Code catches invented facts; the Reviewer
catches spin. Together they cover more than either alone.
"""

from __future__ import annotations
import re
import sys
import argparse
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("Missing dependency: pip install pyyaml\n")
    sys.exit(2)


# ── Load frozen facts ────────────────────────────────────────────────────────
def load_facts(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def known_strings(facts: dict) -> set[str]:
    """Every proper noun / credential the document is allowed to assert."""
    out: set[str] = set()
    cand = facts.get("candidate") or {}
    if cand.get("name"):
        out.add(cand["name"].strip().lower())
    for p in facts.get("projects") or []:
        if p.get("name"):
            out.add(p["name"].strip().lower())
    for t in facts.get("tools") or []:
        if t:
            out.add(t.strip().lower())
    for e in facts.get("employers") or []:
        for k in ("company", "title"):
            if e.get(k):
                out.add(e[k].strip().lower())
    for ed in facts.get("education") or []:
        for k in ("institution", "credential"):
            if ed.get(k):
                out.add(ed[k].strip().lower())
    for c in facts.get("certifications") or []:
        if c.get("name"):
            out.add(c["name"].strip().lower())
    for s in facts.get("skills") or []:
        if s:
            out.add(s.strip().lower())
    return {s for s in out if s}


def known_numbers(facts: dict) -> set[str]:
    """Every numeric value in the facts, normalised (trailing % stripped)."""
    blob = yaml.safe_dump(facts)
    return {t.rstrip("%") for t in re.findall(r"\d+(?:\.\d+)?%?", blob)}


def known_credentials(facts: dict) -> set[str]:
    """Only degrees and certifications — the vocabulary a credential claim may use."""
    out: set[str] = set()
    for ed in facts.get("education") or []:
        if ed.get("credential"):
            out.add(ed["credential"].strip().lower())
    for c in facts.get("certifications") or []:
        if c.get("name"):
            out.add(c["name"].strip().lower())
    return {s for s in out if s}


# ── Checks ───────────────────────────────────────────────────────────────────
# Capitalised multi-word phrases are candidate org/credential names.
# No '.' inside, and we split on sentence/line boundaries before matching.
ORG_LIKE = re.compile(r"\b([A-Z][a-zA-Z0-9&]+(?:\s+[A-Z][a-zA-Z0-9&]+){1,3})\b")
CERT_CUES = re.compile(r"\b(certified|certificate|certification|PMP|CSPO|CSM|MBA|PhD)\b", re.I)
METRIC = re.compile(r"\b\d+(?:\.\d+)?%?\b")

# Words that look capitalised but are never a fabrication signal.
STOPWORDS = {
    "i", "the", "a", "an", "and", "or", "but", "product", "manager", "senior", "lead",
    "staff", "group", "team", "teams", "roadmap", "strategy", "ai", "ml", "pm", "led",
    "built", "owned", "drove", "shipped", "monday", "tuesday", "wednesday", "thursday",
    "friday", "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "dear", "sincerely", "regards",
}


def _sentences(text: str) -> list[str]:
    """Split on sentence and line boundaries so a phrase never spans them."""
    return [s for s in re.split(r"[.\n!?;:]+", text) if s.strip()]


def check(document: str, facts: dict) -> list[str]:
    findings: list[str] = []
    known = known_strings(facts)
    creds = known_credentials(facts)
    nums = known_numbers(facts)

    # 1) Certification cues not backed by a known degree/certification.
    for m in CERT_CUES.finditer(document):
        window = document[max(0, m.start() - 30): m.end() + 30].lower()
        if not any(c in window for c in creds):
            snippet = document[max(0, m.start() - 20): m.end() + 20].strip().replace("\n", " ")
            findings.append(f"Uncredentialed certification cue near: '...{snippet}...'")

    # 2) Org-like proper nouns not present in the facts (checked per sentence).
    for sentence in _sentences(document):
        for m in ORG_LIKE.finditer(sentence):
            phrase = m.group(1).strip()
            low = phrase.lower()
            if all(w in STOPWORDS for w in low.split()):
                continue
            if low not in known and not any(low in k or k in low for k in known):
                findings.append(f"Unverified proper noun (possible invented entity): '{phrase}'")

    # 3) Hard metrics not derivable from the facts (normalised compare).
    for m in METRIC.finditer(document):
        token = m.group(0).rstrip("%")
        if token not in nums:
            window = document[max(0, m.start() - 30): m.end() + 30].strip().replace("\n", " ")
            findings.append(f"Metric '{m.group(0)}' has no basis in career_facts.yaml — near: '...{window}...'")

    # De-dupe while preserving order.
    seen, unique = set(), []
    for f in findings:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


# ── CLI ──────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Code-enforced honesty gate.")
    ap.add_argument("document", help="Path to the generated document to check.")
    ap.add_argument("--facts", default="career_facts.yaml", help="Path to frozen facts.")
    args = ap.parse_args()

    doc_path, facts_path = Path(args.document), Path(args.facts)
    if not doc_path.exists():
        sys.stderr.write(f"Document not found: {doc_path}\n"); return 2
    if not facts_path.exists():
        sys.stderr.write(f"Facts not found: {facts_path}\n"); return 2

    facts = load_facts(facts_path)
    findings = check(doc_path.read_text(encoding="utf-8"), facts)

    if findings:
        print("HONESTY GATE FAILED — review before this leaves the system:\n")
        for f in findings:
            print(f"  ⚠  {f}")
        print(f"\n{len(findings)} item(s) to resolve. Fix the document, not the facts.")
        return 1

    print("Honesty gate passed: no unverified entities, credentials, or metrics found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
