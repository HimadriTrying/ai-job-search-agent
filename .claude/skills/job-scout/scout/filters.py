"""
filters.py — hard drops applied BEFORE any scoring/LLM call. Out-of-band roles are removed,
not scored low and kept: no LLM call is ever spent on a role that can never qualify.

Order in run.py: keyword prefilter -> seniority floor -> experience gate -> location/excludes.
Each returns (passed: bool, reason: str) so the digest can explain every drop.
"""

from __future__ import annotations
import re

# "8 years" style, capturing the number.
_YEARS = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.I)
# Hard cue words that make a minimum a real gate.
_HARD_CUE = re.compile(r"\b(required|must|minimum|at least|no less than)\b", re.I)
# Soft phrasing that should NOT trigger a drop.
_SOFT_CUE = re.compile(r"\b(preferred|nice to have|or equivalent|plus|bonus|ideally)\b", re.I)


def experience_gate(text: str, candidate_years: int) -> tuple[bool, str]:
    """
    Drop only when a minimum is HARD-CUED and above the candidate's years.
    "8 years required" with a 5-yr candidate -> drop.
    "8+ years preferred (or equivalent)" or a bare "8 years" -> survive.
    """
    for m in _YEARS.finditer(text):
        years = int(m.group(1))
        if years <= candidate_years:
            continue
        # Look at the surrounding clause for cue words.
        window = text[max(0, m.start() - 60): m.end() + 60]
        if _HARD_CUE.search(window) and not _SOFT_CUE.search(window):
            return False, f"hard-cued minimum {years}y > your {candidate_years}y"
    return True, "experience ok"


def keyword_prefilter(title: str, must_have: list[str]) -> tuple[bool, str]:
    """Cheap pre-LLM gate: if a must-have list is set, the title must hit at least one."""
    if not must_have:
        return True, "no must-have set"
    t = title.lower()
    if any(k.lower() in t for k in must_have):
        return True, "title matched a must-have keyword"
    return False, "title matched no must-have keyword"


def location_gate(location: str, required: list[str], remote_ok_terms=("remote", "anywhere")) -> tuple[bool, str]:
    """If required locations are set, the job location must match one (or be remote)."""
    if not required:
        return True, "no location constraint"
    loc = (location or "").lower()
    if any(term in loc for term in remote_ok_terms):
        return True, "remote"
    if any(r.lower() in loc for r in required):
        return True, "location matched"
    return False, f"location '{location}' not in {required}"


def industry_gate(text: str, excluded: list[str]) -> tuple[bool, str]:
    """Drop if any excluded-industry keyword appears."""
    if not excluded:
        return True, "no exclusions"
    t = (text or "").lower()
    hit = next((e for e in excluded if e.lower() in t), None)
    if hit:
        return False, f"excluded industry cue: '{hit}'"
    return True, "industry ok"
