"""
scoring.py — penalty-first rubric scorer.

A rubric that says yes to everything is not a filter. So this starts at 0
and mostly SUBTRACTS. Bonuses are small and few, keeping the rubric net-negative. Every
adjustment carries a human-readable reason so the digest explains itself.

This runs only on roles that already survived the hard drops in filters.py.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field


@dataclass
class Verdict:
    score: int
    reasons: list[str] = field(default_factory=list)
    bucket: str = "skipped"


def _contains_any(text: str, terms: list[str]) -> list[str]:
    """Word-boundary matching. Substring matching made 'ai' hit 'email'/'available'
    and put near-every JD in the top bucket — a term only counts as a whole word."""
    t = (text or "").lower()
    return [k for k in terms
            if k.strip() and re.search(rf"(?<!\w){re.escape(k.strip().lower())}(?!\w)", t)]


def _strip_html(text: str) -> str:
    """Greenhouse ships raw HTML in `content`; tags and entities must not feed the
    keyword matcher."""
    return re.sub(r"&[a-z#0-9]+;", " ", re.sub(r"<[^>]+>", " ", text or ""))


def score_job(job: dict, cfg: dict) -> Verdict:
    """
    job: normalized dict with title, description, location, department, comp (optional).
    cfg: rubric config (see config.example.yaml). Returns a Verdict.
    """
    text = _strip_html(f"{job.get('title','')} {job.get('description','')}").strip()
    reasons: list[str] = []
    score = 0

    # ---- Penalties (subtract) --------------------------------------------------
    vague = job.get("description") and len(job["description"]) < 400
    if vague:
        score -= 2; reasons.append("-2 vague/boilerplate JD (very short)")

    # A 'senior' title whose body never mentions strategy/direction = IC in disguise.
    senior_title = any(w in job.get("title", "").lower() for w in ("senior", "lead", "staff", "principal", "group"))
    has_direction = _contains_any(text, ["strategy", "vision", "roadmap", "direction", "influence", "cross-functional", "cross functional"])
    if senior_title and not has_direction:
        score -= 2; reasons.append("-2 senior title but no strategy/direction language")

    missing_stack = cfg.get("unfamiliar_stack", [])
    if _contains_any(text, missing_stack):
        score -= 2; reasons.append("-2 leans on an unfamiliar core stack")

    # ---- Bonuses (add sparingly) ----------------------------------------------
    ai_terms = cfg.get("ai_terms", ["ai", "ml", "llm", "genai", "machine learning"])
    if _contains_any(text, ai_terms):
        score += 2; reasons.append("+2 AI-forward / on-target for AI-builder roles")

    altitude = _contains_any(text, ["set the vision", "define strategy", "0 to 1", "0-to-1", "company strategy", "org-wide", "multiple teams"])
    if altitude:
        score += 2; reasons.append("+2 explicit Staff/Group altitude signal")

    nice = _contains_any(text, cfg.get("nice_to_have_keywords", []))
    if nice:
        score += 1; reasons.append(f"+1 matched nice-to-have: {', '.join(nice[:3])}")

    if job.get("warm_path"):
        score += 2; reasons.append("+2 warm intro path exists (from network-mapper)")

    # Comp below floor, only if disclosed.
    comp = job.get("comp_max")
    floor = cfg.get("comp_floor")
    if comp is not None and floor is not None and comp < floor:
        score -= 2; reasons.append(f"-2 disclosed comp {comp} below floor {floor}")

    # ---- Bucket ---------------------------------------------------------------
    apply_at = cfg.get("apply_first_at", 2)
    look_at = cfg.get("worth_a_look_at", 0)
    if score >= apply_at:
        bucket = "apply first"
    elif score >= look_at:
        bucket = "worth a look"
    else:
        bucket = "skipped"
    return Verdict(score=score, reasons=reasons, bucket=bucket)
