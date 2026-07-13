"""
Offline tests for the Job Scout. No network. Run:  python -m pytest -q   (or python tests/test_scout.py)
Covers the parts that must be right before this touches real applications.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

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
