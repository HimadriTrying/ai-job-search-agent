#!/usr/bin/env python3
"""
verify.py — the code-enforced honesty gate.

The single most important guarantee in this system: no outbound document may contain
an employer, title, credential, or hard metric that is not present in career_facts.yaml.

The AI reframes and reorders what is already true. This script proves it did not invent.
It is deliberately a *separate program* from the thing that writes the document — a prompt
that says "don't fabricate" is a promise; this is a check.

Usage:
    python honesty/verify.py <document.md|.txt|.tex>                # check one doc
    python honesty/verify.py --facts career_facts.yaml <doc>        # explicit facts path
    python honesty/verify.py --target "Acme Robotics" <doc>         # company being applied to
    python honesty/verify.py --job posting.txt <doc>                # the JD the doc responds to

A cover letter legitimately names the company it addresses and details from the posting.
Those are not fabrications about the candidate — declare them with --target / --job so the
gate can tell "references the role" apart from "invents a fact".

Exit codes:
    0  = clean
    1  = potential fabrication found (fails loudly; the doc must be fixed, not the facts)
    2  = usage / file error

Design notes
------------
This is intentionally conservative: it FLAGS for human review rather than silently passing.
Three properties matter and are covered by tests (tests/test_verify.py):

1.  Numbers are claim-scoped. Allowed metrics come only from fields that carry claims
    (employer metrics/scope/dates, education and certification years) — never from
    candidate contact details. A phone number is not evidence for a growth percentage.
2.  Numbers are attributed. Inside a sentence that names exactly one known employer, a
    metric must come from THAT employer's record. Real numbers moved to the wrong employer
    are the most common form of résumé drift, and membership-only checks miss it.
3.  Known-term matching is word-boundary based. A short skill like "sql" whitelists "SQL",
    not every phrase that happens to contain those letters.

It cannot catch every possible embellishment — pair it with the fresh-context Reviewer
subagent, which reads for framing and tone. Code catches invented facts; the Reviewer
catches spin. Together they cover more than either alone.
"""

from __future__ import annotations
import re
import sys
import argparse
from dataclasses import dataclass, field
from datetime import date
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


# ── Context: what this document is allowed to reference beyond the facts ─────
@dataclass
class Context:
    """Role-specific references (target company, JD vocabulary) that are legitimate
    in an outbound document even though they are not facts about the candidate."""
    targets: list[str] = field(default_factory=list)   # e.g. ["Acme Robotics"]
    known: set[str] = field(default_factory=set)       # extra allowed phrases, lowered
    numbers: set[str] = field(default_factory=set)     # extra allowed numbers, normalised

    def all_known(self) -> set[str]:
        return self.known | {t.strip().lower() for t in self.targets if t.strip()}


def context_from_job_posting(text: str, targets: list[str] | None = None) -> Context:
    """Anything the posting itself says — org names, team names, its own numbers —
    is fair game for a document responding to that posting."""
    ctx = Context(targets=list(targets or []))
    for m in ORG_LIKE.finditer(text):
        ctx.known.add(m.group(1).strip().lower())
    ctx.numbers |= {_norm_num(t) for t in NUM_TOKEN.findall(text)}
    return ctx


# ── Extracting allowed strings / numbers from the facts ──────────────────────
def known_strings(facts: dict) -> set[str]:
    """Every proper noun / credential the document is allowed to assert."""
    out: set[str] = set()
    cand = facts.get("candidate") or {}
    for k in ("name", "location"):
        if cand.get(k):
            out.add(str(cand[k]).strip().lower())
    for e in facts.get("employers") or []:
        for k in ("company", "title"):
            if e.get(k):
                out.add(e[k].strip().lower())
        # Fact TEXT is quotable, not just fact names: a proper noun the user
        # literally wrote in their own metrics/scope ("IBM Cloud", "Investor
        # Club") is not an invention when a document reuses it. Numbers are
        # unaffected — claim_numbers() keeps its own scoping.
        for line in list(e.get("metrics") or []) + list(e.get("scope") or []):
            if line:
                out.add(str(line).strip().lower())
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
    for c in facts.get("coaching") or []:
        for k in ("organisation", "role"):
            if c.get(k):
                out.add(str(c[k]).strip().lower())
        for line in c.get("metrics") or []:
            if line:
                out.add(str(line).strip().lower())
    for line in _endurance_lines(facts):
        out.add(line.strip().lower())
    return {s for s in out if s}


def _endurance_lines(facts: dict) -> list[str]:
    """Endurance entries are plain strings, except a trailing {note: ...} dict."""
    out: list[str] = []
    for item in facts.get("endurance") or []:
        if isinstance(item, dict):
            out += [str(v) for v in item.values() if v]
        elif item:
            out.append(str(item))
    return out


NUM_TOKEN = re.compile(r"\d+(?:\.\d+)?%?")


def _norm_num(tok: str) -> str:
    """Canonical form for comparing numbers: '18%' == '18', '07' == '7'."""
    t = tok.rstrip("%")
    if t.isdigit():
        t = str(int(t))
    return t


def _nums_in(*texts) -> set[str]:
    out: set[str] = set()
    for t in texts:
        if t:
            out |= {_norm_num(x) for x in NUM_TOKEN.findall(str(t))}
    return out


def _parse_ym(s: str) -> tuple[int, int] | None:
    m = re.match(r"^\s*(\d{4})(?:-(\d{1,2}))?\s*$", str(s or ""))
    if not m:
        return None
    return int(m.group(1)), int(m.group(2) or 1)


def _tenure_years(start: str, end: str) -> set[str]:
    """Whole-year durations derivable from an employment range ('3 years at X')."""
    s = _parse_ym(start)
    e = (date.today().year, date.today().month) if str(end).strip().lower() == "present" \
        else _parse_ym(end)
    if not s or not e:
        return set()
    months = max(0, (e[0] - s[0]) * 12 + (e[1] - s[1]))
    lo, hi = months // 12, round(months / 12)
    return {str(lo), str(hi)}


def claim_numbers(facts: dict) -> tuple[dict[str, set[str]], set[str]]:
    """Numbers a document may assert, scoped to where they come from.

    Returns (per_employer, shared):
      per_employer["acme corp"] = numbers from THAT employer's metrics/scope/dates/tenure
      shared                    = employer-independent numbers (education, certifications,
                                  coaching, endurance)

    Deliberately excluded: candidate.contact (phone, email, links). Contact digits are
    identity data, not evidence — treating them as metrics is how a phone number ends up
    "supporting" a fake growth percentage.

    Coaching and endurance are shared, not per-employer: they are claims about the
    candidate that no employer owns. They were absent here until 6 Aug 2026, which made
    the gate fail true facts — "204 classes" and "3 Hyrox open races" were in the facts
    file and still flagged. A gate that rejects the truth teaches people to override it,
    so this omission was a safety bug, not a conservative default.
    """
    per: dict[str, set[str]] = {}
    for e in facts.get("employers") or []:
        nums = _nums_in(*(e.get("metrics") or []), *(e.get("scope") or []),
                        e.get("start"), e.get("end"), e.get("title"))
        nums |= _tenure_years(e.get("start", ""), e.get("end", ""))
        per[(e.get("company") or "").strip().lower()] = nums
    shared: set[str] = set()
    for ed in facts.get("education") or []:
        shared |= _nums_in(ed.get("year"), ed.get("credential"), ed.get("institution"))
    for c in facts.get("certifications") or []:
        shared |= _nums_in(c.get("year"), c.get("name"))
    for c in facts.get("coaching") or []:
        shared |= _nums_in(*(c.get("metrics") or []),
                           c.get("period"), c.get("cadence"), c.get("role"))
    shared |= _nums_in(*_endurance_lines(facts))
    return per, shared


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
# "self-certification" / "self-certified" are regulatory process vocabulary
# (e.g. FCA self-certification), not claims of holding a credential.
CERT_CUES = re.compile(r"(?<!self-)\b(certified|certificate|certification|PMP|CSPO|CSM|MBA|PhD)\b", re.I)
METRIC = re.compile(r"\b\d+(?:\.\d+)?%?\b")

# Words that look capitalised but are never a fabrication signal.
STOPWORDS = {
    "i", "the", "a", "an", "and", "or", "but", "product", "manager", "senior", "lead",
    "staff", "group", "team", "teams", "roadmap", "strategy", "ai", "ml", "pm", "led",
    "built", "owned", "drove", "shipped", "monday", "tuesday", "wednesday", "thursday",
    "friday", "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "dear", "sincerely", "regards",
    "hiring", "kind", "best", "warm", "yours", "faithfully", "committee", "sir", "madam",
}

# Whole letter-furniture phrases, never claims about the candidate.
LETTER_PHRASES = {
    "dear hiring manager", "dear hiring team", "hiring manager", "hiring team",
    "dear sir or madam", "to whom it may concern", "kind regards", "best regards",
    "warm regards", "yours sincerely", "yours faithfully", "thank you",
}


def _sentences(text: str) -> list[str]:
    """Split on sentence and line boundaries so a phrase never spans them."""
    return [s for s in re.split(r"[.\n!?;:]+", text) if s.strip()]


def _word_match(needle: str, haystack: str) -> bool:
    """True if needle occurs in haystack on word boundaries (both lowered)."""
    return re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack) is not None


def _phrase_is_known(low: str, known: set[str]) -> bool:
    """A phrase is known if it equals a known term, contains one, or is contained by
    one — always on word boundaries. 'sql' matches 'SQL Server'; it does NOT match
    'Air France' just because the letters appear inside other words."""
    if low in known:
        return True
    return any(_word_match(k, low) or _word_match(low, k) for k in known)


def check(document: str, facts: dict, context: Context | None = None) -> list[str]:
    findings: list[str] = []
    ctx = context or Context()
    known = known_strings(facts) | ctx.all_known()
    creds = known_credentials(facts)
    per_employer, shared_nums = claim_numbers(facts)
    all_claim_nums = shared_nums | set().union(*per_employer.values()) if per_employer \
        else set(shared_nums)
    employer_names = [k for k in per_employer if k]

    # 1) Certification cues not backed by a known degree/certification.
    for m in CERT_CUES.finditer(document):
        window = document[max(0, m.start() - 30): m.end() + 30].lower()
        if not any(c in window for c in creds):
            snippet = document[max(0, m.start() - 20): m.end() + 20].strip().replace("\n", " ")
            findings.append(f"Uncredentialed certification cue near: '...{snippet}...'")

    for sentence in _sentences(document):
        low_sentence = sentence.lower()

        # 2) Org-like proper nouns not present in facts or declared context.
        for m in ORG_LIKE.finditer(sentence):
            phrase = m.group(1).strip()
            low = phrase.lower()
            if low in LETTER_PHRASES:
                continue
            if all(w in STOPWORDS for w in low.split()):
                continue
            if not _phrase_is_known(low, known):
                findings.append(f"Unverified proper noun (possible invented entity): '{phrase}'")

        # 3) Hard metrics: claim-scoped and, where possible, employer-attributed.
        mentioned = [e for e in employer_names if _word_match(e, low_sentence)]
        if len(mentioned) == 1:
            allowed = per_employer[mentioned[0]] | shared_nums | ctx.numbers
        else:
            allowed = all_claim_nums | ctx.numbers
        for m in METRIC.finditer(sentence):
            token = _norm_num(m.group(0))
            if token in allowed:
                continue
            snippet = sentence.strip().replace("\n", " ")[:80]
            if len(mentioned) == 1 and token in all_claim_nums:
                findings.append(
                    f"Metric '{m.group(0)}' is attributed to '{mentioned[0]}' but comes from "
                    f"a different part of career_facts.yaml — near: '...{snippet}...'")
            else:
                findings.append(
                    f"Metric '{m.group(0)}' has no basis in career_facts.yaml — near: '...{snippet}...'")

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
    ap.add_argument("--target", action="append", default=[],
                    help="Company/role being applied to (repeatable). Lets the gate tell "
                         "'references the role' apart from 'invents a fact'.")
    ap.add_argument("--job", default=None,
                    help="Path to the job posting this document responds to; its own names "
                         "and numbers become legitimate references.")
    args = ap.parse_args()

    doc_path, facts_path = Path(args.document), Path(args.facts)
    if not doc_path.exists():
        sys.stderr.write(f"Document not found: {doc_path}\n"); return 2
    if not facts_path.exists():
        sys.stderr.write(f"Facts not found: {facts_path}\n"); return 2

    if args.job:
        job_path = Path(args.job)
        if not job_path.exists():
            sys.stderr.write(f"Job posting not found: {job_path}\n"); return 2
        ctx = context_from_job_posting(job_path.read_text(encoding="utf-8"), targets=args.target)
    else:
        ctx = Context(targets=args.target)

    facts = load_facts(facts_path)
    findings = check(doc_path.read_text(encoding="utf-8"), facts, context=ctx)

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
