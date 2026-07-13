"""
seniority.py — title -> seniority level, and the seniority-floor filter.

Most job filters are built for junior candidates and drop roles that are *too senior*.
This system targets Senior/Lead/Staff/Group, so the filter is a FLOOR, not a ceiling: it
drops everything BELOW Senior. Same title-ladder logic either way; the comparison is `<`.
"""

from __future__ import annotations
import re

# Ordered ladder. Higher number = more senior.
LEVELS = {
    "intern": 0,
    "entry": 1,      # associate / junior / APM / "PM I" / graduate
    "mid": 2,        # a bare "Product Manager" with no seniority qualifier
    "senior": 3,
    "lead": 4,
    "staff": 4,
    "principal": 5,
    "group": 5,
    "director": 6,   # incl. "Head of Product"
    "vp": 7,
    "exec": 8,       # CPO / Chief
}

# Token -> level name. Checked in priority order (first match wins), so more specific
# and more senior cues are tested before generic ones.
_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bchief\b|\bcpo\b", re.I), "exec"),
    (re.compile(r"\bvp\b|vice[-\s]?president", re.I), "vp"),
    (re.compile(r"\bdirector\b|head of product|head of pm", re.I), "director"),
    (re.compile(r"\bgroup\b", re.I), "group"),
    (re.compile(r"\bprincipal\b", re.I), "principal"),
    (re.compile(r"\bstaff\b", re.I), "staff"),
    (re.compile(r"\blead\b|\bleader\b", re.I), "lead"),
    (re.compile(r"\bsenior\b|\bsr\.?\b", re.I), "senior"),
    (re.compile(r"\bassociate\b|\bjunior\b|\bjr\.?\b|\bapm\b|\bpm\s*i\b|graduate|early[-\s]?career", re.I), "entry"),
    (re.compile(r"\bintern\b|internship", re.I), "intern"),
]


def classify_level(title: str) -> tuple[int, str]:
    """Return (level_int, level_name). A product/PM title with no seniority cue = 'mid'."""
    for pat, name in _PATTERNS:
        if pat.search(title):
            return LEVELS[name], name
    # No explicit cue. If it's a product role at all, it's a bare/mid PM.
    if re.search(r"product manager|product owner|\bpm\b|product lead", title, re.I):
        return LEVELS["mid"], "mid"
    return LEVELS["mid"], "unknown"


def passes_seniority(
    title: str,
    min_level: str = "senior",
    max_level: str | None = None,
    keep_ambiguous: bool = False,
) -> tuple[bool, str]:
    """
    True if the title is AT OR ABOVE the floor (and at/below ceiling if set).
    `keep_ambiguous=True` lets a bare 'Product Manager' through even under a Senior floor.
    Returns (passes, reason).
    """
    lvl, name = classify_level(title)
    floor = LEVELS[min_level]
    if name in ("mid", "unknown") and keep_ambiguous:
        return True, f"ambiguous level ({name}) kept by config"
    if lvl < floor:
        return False, f"below floor: '{name}' (<{min_level})"
    if max_level is not None and lvl > LEVELS[max_level]:
        return False, f"above ceiling: '{name}' (>{max_level})"
    return True, f"level ok: '{name}'"
