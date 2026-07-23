#!/usr/bin/env python3
"""
run.py — the Job Scout entry point.

Pipeline (per CLAUDE.md / SKILL.md):
  sweep watchlist -> keyword prefilter -> hard drops (seniority, experience, location,
  industry) -> penalty score survivors -> sort into apply-first / worth-a-look / skipped ->
  write dated digest to data/digests/.

Usage:
  python run.py                         # live sweep using config.yaml (or config.example.yaml)
  python run.py --offline fixtures.json # score a saved payload; no network (for testing/CI)
"""

from __future__ import annotations
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scout import ats, filters, scoring  # noqa: E402

try:
    import yaml
except ImportError:
    print("pip install pyyaml"); raise

HERE = Path(__file__).parent
REPO = HERE.parents[2]  # .../ai-job-search-orchestrator
DIGESTS = REPO / "data" / "digests"


def load_config() -> dict:
    for name in ("config.yaml", "config.example.yaml"):
        p = HERE / name
        if p.exists():
            return yaml.safe_load(p.read_text()) or {}
    return {}


def load_watchlist() -> list[str]:
    for name in ("watchlist.txt", "watchlist.example.txt"):
        p = HERE / name
        if p.exists():
            return [ln.strip() for ln in p.read_text().splitlines()
                    if ln.strip() and not ln.startswith("#")]
    return []


def backfill_sr_descriptions(jobs: list[dict], cfg: dict,
                             fetch=None) -> int:
    """SmartRecruiters list results carry no description, which let those roles dodge
    every description-based gate, penalty, and bonus — they scored a constant 0.
    Fetch the posting detail, but only for jobs whose title already passes the cheap
    title-only gates, so the sweep stays cheap. Returns how many fetches came back empty
    (those roles are still scored, just without a description — disclosed in the digest).
    """
    from scout.seniority import passes_seniority
    fetch = fetch or ats.fetch_sr_description
    failed = 0
    for j in jobs:
        if j.get("source") != "smartrecruiters" or j.get("description"):
            continue
        if not filters.keyword_prefilter(j.get("title", ""), cfg.get("must_have_keywords", []))[0]:
            continue
        if not passes_seniority(j.get("title", ""), cfg.get("min_seniority", "senior"),
                                cfg.get("max_seniority"), cfg.get("keep_ambiguous", False))[0]:
            continue
        desc = fetch(j.get("company", ""), j.get("id", ""))
        if desc:
            j["description"] = desc
        else:
            failed += 1
    return failed


def watchlist_health(n_entries: int, n_errors: int, threshold: float = 0.3):
    """A mostly-dead watchlist produces an empty digest that reads like a quiet day.
    Fail the run loudly instead when too many entries error, so slug drift gets fixed
    instead of silently starving discovery. Returns (ok, message)."""
    if n_entries and n_errors / n_entries > threshold:
        return False, (f"{n_errors}/{n_entries} watchlist entries failed to fetch "
                       f"(over {int(threshold * 100)}%). The watchlist looks stale — an empty "
                       "digest would be misleading, so this run fails. Fix the ats:token "
                       "slugs in watchlist.txt (a 404 usually means the board moved).")
    return True, ""


def apply_pipeline(jobs: list[dict], cfg: dict):
    """Return (buckets, dropped) where dropped is a list of (job, reason)."""
    buckets = {"apply first": [], "worth a look": [], "skipped": []}
    dropped = []
    cy = int(cfg.get("candidate_years", 5))
    for j in jobs:
        text = f"{j.get('title','')} {j.get('description','')}"
        ok, why = filters.keyword_prefilter(j.get("title", ""), cfg.get("must_have_keywords", []))
        if not ok:
            dropped.append((j, why)); continue
        # seniority floor (inverted)
        from scout.seniority import passes_seniority
        ok, why = passes_seniority(j.get("title", ""), cfg.get("min_seniority", "senior"),
                                   cfg.get("max_seniority"), cfg.get("keep_ambiguous", False))
        if not ok:
            dropped.append((j, why)); continue
        ok, why = filters.experience_gate(text, cy)
        if not ok:
            dropped.append((j, why)); continue
        ok, why = filters.location_gate(j.get("location", ""), cfg.get("required_locations", []))
        if not ok:
            dropped.append((j, why)); continue
        ok, why = filters.industry_gate(text, cfg.get("excluded_industries", []))
        if not ok:
            dropped.append((j, why)); continue
        v = scoring.score_job(j, cfg)
        buckets[v.bucket].append((j, v))
    for b in buckets:
        buckets[b].sort(key=lambda pair: pair[1].score, reverse=True)
    return buckets, dropped


def write_digest(buckets, dropped, errors) -> Path:
    DIGESTS.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    out = DIGESTS / f"{today}.md"
    lines = [f"# Job Scout digest — {today}", ""]
    for b in ("apply first", "worth a look"):
        lines.append(f"## {b.title()} ({len(buckets[b])})")
        for j, v in buckets[b]:
            lines.append(f"- **{j['title']}** — {j['company']} · {j.get('location','')} "
                         f"(score {v.score:+d})  \n  {j.get('url','')}")
            for r in v.reasons:
                lines.append(f"  - {r}")
        lines.append("")
    lines.append(f"## Skipped ({len(buckets['skipped'])})")
    for j, v in buckets["skipped"][:20]:
        lines.append(f"- {j['title']} — {j['company']} (score {v.score:+d})")
    lines.append("")
    lines.append(f"## Dropped before scoring ({len(dropped)})")
    for j, why in dropped[:30]:
        lines.append(f"- {j.get('title','?')} — {j.get('company','?')}: {why}")
    if errors:
        lines.append("\n## Fetch errors")
        for e in errors:
            lines.append(f"- {e}")
    out.write_text("\n".join(lines))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", help="Path to a JSON list of normalized jobs (skip network).")
    args = ap.parse_args()
    cfg = load_config()

    errors = []
    n_entries = 0
    if args.offline:
        jobs = json.loads(Path(args.offline).read_text())
    else:
        jobs = []
        entries = load_watchlist()
        n_entries = len(entries)
        for entry in entries:
            got, err = ats.fetch_company(entry)
            jobs.extend(got)
            if err:
                errors.append(err)
        n_fetch_errors = len(errors)
        sr_failed = backfill_sr_descriptions(jobs, cfg)
        if sr_failed:
            errors.append(f"smartrecruiters: {sr_failed} posting-detail fetch(es) failed; "
                          "those roles were scored without a description")

    buckets, dropped = apply_pipeline(jobs, cfg)
    path = write_digest(buckets, dropped, errors)
    print(f"Swept {len(jobs)} listings → "
          f"{len(buckets['apply first'])} apply-first, "
          f"{len(buckets['worth a look'])} worth-a-look, "
          f"{len(buckets['skipped'])} skipped, {len(dropped)} dropped.")
    print(f"Digest: {path}")
    if errors:
        print(f"({len(errors)} fetch error(s) — see digest)")
    if not args.offline:
        ok, msg = watchlist_health(n_entries, n_fetch_errors,
                                   float(cfg.get("max_fetch_error_ratio", 0.3)))
        if not ok:
            print(f"ERROR: {msg}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
