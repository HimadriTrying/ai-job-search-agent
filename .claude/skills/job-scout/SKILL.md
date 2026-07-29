---
name: job-scout
description: Discover and score open roles against the user's rubric. Sweeps ATS APIs, drops out-of-band roles before scoring, sorts survivors into apply-first / worth-a-look / skipped. Runs scheduled (daily digest) or on demand.
invocation: auto
---

# job-scout — discovery + scoring

## Precedent
Sweeps public ATS APIs (Greenhouse, Lever, Ashby, SmartRecruiters), hard-drops out-of-band
roles before any LLM call, then scores survivors with a cheap model. Cost scales with matches, not listings.

## Data sources (public ATS APIs — no scraping)
Greenhouse, Lever, Ashby, SmartRecruiters each expose public job-listing endpoints. Maintain
a watchlist of target companies (see `data/` — create `watchlist.txt`). A full sweep of ~100
companies takes about a minute.

## Pipeline
1. Sweep the watchlist via ATS APIs → raw listings.
2. **Keyword pre-filter BEFORE any LLM call** — cheap. Drop obviously off-target roles.
3. **Hard drops** from `profile/04-job-evaluation.md`: `min_seniority` (drop below Senior),
   hard-cued experience minimums, location, work-auth, excluded industries.
4. Score survivors against the rubric (mostly penalties). Use a cheap model for scoring,
   a stronger one only for anything you tailor later — deliberate cost tiering.
5. Sort into **apply first / worth a look / skipped**, one-line reason each.
6. Write a dated digest to `data/digests/YYYY-MM-DD.md` and (if scheduled) commit it.

## Reliability
Malformed scoring output retries once, then marks the role `unscored` rather than crashing
the whole run.

## Mode
Scheduled (daily, cheap, benefits from overnight) via `.github/workflows/daily-scout.yml`,
or on demand when the user asks "what's out there".

## Implementation (built and tested)
Real code lives in `scout/` and `run.py`:
- `scout/ats.py` — keyless public-JSON clients for Greenhouse/Lever/Ashby/SmartRecruiters,
  normalized to one schema. Companies are `ats:token` (e.g. `greenhouse:stripe`).
- `scout/seniority.py` — title→level ladder with the **inverted** floor (drops below Senior).
- `scout/filters.py` — keyword prefilter + hard drops (experience gate fires only on
  hard-cued minimums; location; excluded industries).
- `scout/scoring.py` — penalty-first scorer → score, reasons, bucket.
- `run.py` — orchestrates the pipeline and writes `data/digests/YYYY-MM-DD.md`.

Config: copy `config.example.yaml` → `config.yaml`, set your real years/seniority/locations.
Watchlist: copy `watchlist.example.txt` → `watchlist.txt`, one `ats:token` per line.

Run it live: `python run.py`. With no network at all:

```bash
python run.py --offline tests/fixtures/jobs.sample.json
```

That fixture ships with the repo and exercises the whole pipeline — one apply-first, one
worth-a-look, two skipped, three hard drops, each with its reason — so a first run proves the
scoring works even when the ATS APIs are unreachable.

Tests: `python tests/test_scout.py` — all green. To run live you need network access from
wherever this executes (works locally and in the GitHub Action; not in a sandbox with egress
disabled). Endpoints are current public feeds but slugs drift.

When a live sweep fails, the run names *which* failure it was: a blocked network and a stale
watchlist both fail every fetch, and they need opposite fixes. Network problems point at the
offline command above; slug drift points at `watchlist.txt`.
