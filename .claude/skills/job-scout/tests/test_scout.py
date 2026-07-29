"""
Offline tests for the Job Scout. No network. Run:  python -m pytest -q   (or python tests/test_scout.py)
Covers the parts that must be right before this touches real applications.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import run as scout_run
from scout import seniority, filters, scoring, ats


def test_seniority_inverted_floor():
    # Below Senior -> dropped
    assert seniority.passes_seniority("Associate Product Manager")[0] is False
    assert seniority.passes_seniority("Junior PM")[0] is False
    assert seniority.passes_seniority("Product Manager")[0] is False  # bare = mid, dropped
    # At/above Senior -> kept
    for t in ["Senior Product Manager", "Lead PM", "Staff Product Manager",
              "Group Product Manager", "Principal PM", "Head of Product"]:
        assert seniority.passes_seniority(t)[0] is True, t
    # keep_ambiguous lets a bare PM through
    assert seniority.passes_seniority("Product Manager", keep_ambiguous=True)[0] is True
    # ceiling works
    assert seniority.passes_seniority("VP of Product", max_level="director")[0] is False


def test_experience_gate_hard_vs_soft():
    cand = 5
    assert filters.experience_gate("8+ years required in PM", cand)[0] is False   # hard cue
    assert filters.experience_gate("minimum 10 years of experience", cand)[0] is False
    assert filters.experience_gate("8+ years preferred, or equivalent", cand)[0] is True  # soft
    assert filters.experience_gate("8 years of relevant work", cand)[0] is True   # bare number
    assert filters.experience_gate("3 years required", cand)[0] is True           # below candidate


def test_location_and_industry_gates():
    assert filters.location_gate("Berlin, Germany", ["Berlin"])[0] is True
    assert filters.location_gate("New York", ["Berlin"])[0] is False
    assert filters.location_gate("Remote - EU", ["Berlin"])[0] is True
    assert filters.industry_gate("online casino product", ["gambling", "casino"])[0] is False
    assert filters.industry_gate("fintech payments", ["gambling"])[0] is True


def test_scoring_buckets():
    cfg = {"ai_terms": ["ai", "llm"], "nice_to_have_keywords": ["platform"],
           "apply_first_at": 2, "worth_a_look_at": 0}
    strong = {"title": "Staff Product Manager, AI Platform",
              "description": "Own the company strategy and vision for our LLM platform. " * 20}
    weak = {"title": "Senior Product Manager", "description": "short jd"}
    assert scoring.score_job(strong, cfg).bucket == "apply first"
    # senior title, no direction language, very short -> penalised into skipped
    assert scoring.score_job(weak, cfg).bucket == "skipped"


def test_scoring_matches_whole_words_only():
    cfg = {"ai_terms": ["ai", "ml"], "nice_to_have_keywords": [],
           "apply_first_at": 2, "worth_a_look_at": 0}
    # "Email careers@", "available", "detail" all contain "ai"/"ml" as substrings;
    # none of them is an AI signal. This JD must NOT get the +2 AI bonus.
    billing = {"title": "Senior Product Manager, Billing",
               "description": ("Own the billing roadmap and pricing strategy. Email "
                               "careers@example.com with detail on your background. "
                               "More information available on request. ") * 6}
    v = scoring.score_job(billing, cfg)
    assert not any("AI-forward" in r for r in v.reasons), v.reasons
    assert v.bucket != "apply first"
    # A real whole-word mention still scores.
    real_ai = {"title": "Senior Product Manager, AI Assistants",
               "description": "Set the strategy and roadmap for our AI assistant. " * 12}
    assert any("AI-forward" in r for r in scoring.score_job(real_ai, cfg).reasons)


def test_scoring_ignores_html_markup():
    cfg = {"ai_terms": ["ai"], "nice_to_have_keywords": ["b2b"],
           "apply_first_at": 2, "worth_a_look_at": 0}
    # Greenhouse-style HTML: tags/entities must not create or hide keyword hits.
    job = {"title": "Senior Product Manager",
           "description": ("<div class=\"main\"><p>Drive the <b>AI</b> strategy and roadmap "
                           "for our B2B platform.</p></div>" + "<br/>" * 50 +
                           "<p>Long form description of the role and the team.</p>" * 10)}
    v = scoring.score_job(job, cfg)
    assert any("AI-forward" in r for r in v.reasons)
    assert any("b2b" in r for r in v.reasons)


def test_sr_posting_detail_parser():
    detail = {"jobAd": {"sections": {
        "jobDescription": {"text": "<p>Own the AI roadmap for the platform.</p>"},
        "qualifications": {"text": "8+ years of product experience."}}}}
    text = ats.sr_description_from_posting(detail)
    assert "Own the AI roadmap" in text and "8+ years" in text
    assert ats.sr_description_from_posting({}) == ""


def test_sr_description_backfill_is_gated_and_disclosed():
    jobs = [
        # senior SR role with no description -> gets a detail fetch
        {"source": "smartrecruiters", "company": "acme", "id": "1",
         "title": "Senior Product Manager", "description": ""},
        # junior SR role -> title gate fails, no fetch spent on it
        {"source": "smartrecruiters", "company": "acme", "id": "2",
         "title": "Junior PM", "description": ""},
        # senior SR role whose detail fetch fails -> counted, not fatal
        {"source": "smartrecruiters", "company": "acme", "id": "3",
         "title": "Staff Product Manager", "description": ""},
        # non-SR job -> untouched
        {"source": "greenhouse", "company": "acme", "id": "4",
         "title": "Senior PM", "description": "already present"},
    ]
    calls = []
    def fake_fetch(company, pid):
        calls.append(pid)
        return "" if pid == "3" else f"full text for {pid}"
    failed = scout_run.backfill_sr_descriptions(jobs, {}, fetch=fake_fetch)
    assert calls == ["1", "3"]            # junior + greenhouse never fetched
    assert failed == 1                    # the empty detail is disclosed, not fatal
    assert jobs[0]["description"] == "full text for 1"
    assert jobs[1]["description"] == ""
    assert jobs[3]["description"] == "already present"


def test_watchlist_health_threshold():
    ok, _ = scout_run.watchlist_health(10, 0)
    assert ok is True
    ok, _ = scout_run.watchlist_health(10, 3)          # exactly at 30% -> still ok
    assert ok is True
    ok, msg = scout_run.watchlist_health(10, 4)        # over 30% -> fail loudly
    assert ok is False and "watchlist" in msg
    ok, _ = scout_run.watchlist_health(0, 0)           # empty watchlist -> no divide, no fail
    assert ok is True


def test_watchlist_health_names_the_real_cause():
    """A blocked network and a stale watchlist both fail every fetch, and the first live
    run on a restricted network was told to go fix slugs that were fine. The advice has to
    follow the failure kind, not the count."""
    net = [ats.FetchError("network", "greenhouse:x: URLError: tunnel failed")] * 4
    ok, msg = scout_run.watchlist_health(10, 4, errors=net)
    assert ok is False
    assert "network" in msg and "--offline" in msg
    assert "slug" not in msg              # must NOT send them off to edit the watchlist

    gone = [ats.FetchError("missing", "greenhouse:x: HTTP 404")] * 4
    ok, msg = scout_run.watchlist_health(10, 4, errors=gone)
    assert ok is False and "slug" in msg

    bad = [ats.FetchError("config", "bad watchlist entry")] * 4
    ok, msg = scout_run.watchlist_health(10, 4, errors=bad)
    assert ok is False and "ats:token" in msg

    ok, msg = scout_run.watchlist_health(10, 4, errors=net[:2] + gone[:2])
    assert ok is False and "mixed" in msg

    # No classification available -> still fails, just without a specific diagnosis.
    ok, msg = scout_run.watchlist_health(10, 4, errors=None)
    assert ok is False and msg


def test_classify_exception_separates_network_from_missing():
    import urllib.error
    import socket

    def http(code):
        return urllib.error.HTTPError("http://x", code, "err", {}, None)

    assert ats.classify_exception(http(404)) == "missing"
    assert ats.classify_exception(http(410)) == "missing"
    assert ats.classify_exception(http(403)) == "network"   # proxy denying CONNECT
    assert ats.classify_exception(http(407)) == "network"
    assert ats.classify_exception(http(500)) == "other"
    assert ats.classify_exception(
        urllib.error.URLError("Tunnel connection failed: 403 Forbidden")) == "network"
    assert ats.classify_exception(
        urllib.error.URLError(socket.gaierror(-2, "Name or service not known"))) == "network"
    assert ats.classify_exception(TimeoutError("timed out")) == "network"
    assert ats.classify_exception(ValueError("bad json")) == "other"


def test_vague_penalty_measures_text_not_markup():
    """Greenhouse ships descriptions as HTML. Measuring raw string length counted tags as
    content, so an identical threadbare JD scored -2 plain and 0 wrapped in a div, which
    disabled this penalty for the largest single source of listings."""
    text = "Own the roadmap."
    padded = ('<div class="content"><p style="margin:0">' + text + "</p>"
              + '<span class="x"></span>' * 30 + "</div>")
    assert len(padded) > 400                      # the markup alone clears the threshold

    def vague(desc):
        v = scoring.score_job({"title": "Senior Product Manager", "description": desc}, {})
        return any("vague" in r for r in v.reasons)

    assert vague(text) is True
    assert vague(padded) is True                  # markup must not buy its way out
    # A genuinely substantial HTML JD is still not flagged: widening must not overshoot.
    assert vague("<div>" + ("We own strategy and roadmap for the platform team. " * 10)
                 + "</div>") is False


def test_offline_fixture_ships_and_exercises_every_bucket():
    """`--offline` is the documented fallback when the network is blocked, so the fixture
    it names has to exist, and it has to show the pipeline actually sorting."""
    fixture = Path(__file__).parent / "fixtures" / "jobs.sample.json"
    assert fixture.exists(), "documented --offline fixture is missing"
    jobs = json.loads(fixture.read_text())
    cfg = {"candidate_years": 5,
           "nice_to_have_keywords": ["platform", "0 to 1", "growth", "b2b"]}
    buckets, dropped = scout_run.apply_pipeline(jobs, cfg)
    assert buckets["apply first"], "fixture should surface at least one apply-first role"
    assert dropped, "fixture should show the hard drops firing"
    reasons = " ".join(w for _, w in dropped)
    assert "below floor" in reasons                # seniority floor demonstrated
    assert "hard-cued minimum" in reasons          # experience gate demonstrated


def test_ats_normalizers():
    gh = {"jobs": [{"id": 1, "title": "Senior PM", "location": {"name": "Berlin"},
                    "departments": [{"name": "Product"}], "absolute_url": "http://x", "content": "desc"}]}
    n = ats.normalize("greenhouse", gh, "acme")[0]
    assert n["title"] == "Senior PM" and n["location"] == "Berlin" and n["source"] == "greenhouse"

    lever = [{"id": "a", "text": "Lead PM", "categories": {"location": "Remote", "team": "Core"},
              "hostedUrl": "http://y", "descriptionPlain": "d"}]
    n = ats.normalize("lever", lever, "acme")[0]
    assert n["title"] == "Lead PM" and n["department"] == "Core"

    ashby = {"jobs": [{"id": "b", "title": "Staff PM", "isListed": True, "location": "NYC",
                       "jobUrl": "http://z", "descriptionPlain": "d"}]}
    assert ats.normalize("ashby", ashby, "acme")[0]["title"] == "Staff PM"
    # unlisted filtered out
    ashby2 = {"jobs": [{"id": "c", "title": "Hidden", "isListed": False}]}
    assert ats.normalize("ashby", ashby2, "acme") == []

    sr = {"content": [{"id": "d", "name": "Group PM", "location": {"city": "Berlin", "country": "DE"},
                       "department": {"label": "Product"}, "ref": "http://s"}]}
    assert ats.normalize("smartrecruiters", sr, "acme")[0]["location"] == "Berlin, DE"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn(); passed += 1; print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} tests passed")
