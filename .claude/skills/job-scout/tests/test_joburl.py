"""
Offline tests for joburl.py. No network. Run:  python -m pytest -q

Every case here is a URL shape that has actually turned up in the funnel, plus the
mutations that prove each guard fires. The two that matter most:

  * the embedded-board case (a company's own careers page with ?ashby_jid=), which is the
    shape that forced manual pasting in the first place;
  * the refusals. A resolver that silently returns the wrong posting is worse than one
    that returns nothing, because the wrong JD produces a confidently mis-tailored CV.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from scout import joburl

MOSS_EMBED = "https://www.getmoss.com/careers?ashby_jid=4f998822-03f1-4b31-ac48-928b5e2122a7#open-roles"
MOSS_JID = "4f998822-03f1-4b31-ac48-928b5e2122a7"


# ---- detection -----------------------------------------------------------------
def test_detects_hosted_boards():
    assert joburl.detect_ats("https://jobs.ashbyhq.com/duna/8e5d65f5-3487-442a-ba47-3983e0d54b51") == "ashby"
    assert joburl.detect_ats("https://boards.greenhouse.io/stripe/jobs/4321") == "greenhouse"
    assert joburl.detect_ats("https://job-boards.greenhouse.io/stripe/jobs/4321") == "greenhouse"
    assert joburl.detect_ats("https://jobs.lever.co/palantir/abc-123") == "lever"
    assert joburl.detect_ats("https://careers.smartrecruiters.com/Acme/12345") == "smartrecruiters"


def test_detects_embedded_board_on_company_domain():
    # The whole point: nothing in the host says "ashby", only the query param does.
    assert joburl.detect_ats(MOSS_EMBED) == "ashby"
    assert joburl.detect_ats("https://acme.com/jobs?gh_jid=999") == "greenhouse"


def test_ignores_non_ats_urls():
    for url in ["https://www.linkedin.com/jobs/view/123456",
                "https://example.com/careers",
                "https://news.ycombinator.com/item?id=1"]:
        assert joburl.detect_ats(url) is None, url
        assert joburl.parse(url) is None, url


# ---- token guessing ------------------------------------------------------------
def test_hosted_token_comes_from_the_path():
    assert joburl.candidate_tokens("https://jobs.ashbyhq.com/duna/8e5d65f5") == ["duna"]
    assert joburl.candidate_tokens("https://jobs.lever.co/palantir/abc") == ["palantir"]


def test_embedded_token_is_guessed_from_the_domain():
    # getmoss.com -> the real Ashby board is "moss", reachable by stripping "get".
    tokens = joburl.candidate_tokens(MOSS_EMBED)
    assert tokens[0] == "getmoss"
    assert "moss" in tokens, tokens


def test_token_guessing_skips_ats_subdomains():
    # "jobs"/"careers"/"www" are the product, never the customer's board name.
    assert "www" not in joburl.candidate_tokens(MOSS_EMBED)
    assert "jobs" not in joburl.candidate_tokens("https://jobs.acme.com/x?gh_jid=1")


# ---- job id --------------------------------------------------------------------
def test_job_id_from_embed_param_and_from_path():
    assert joburl.job_id(MOSS_EMBED) == MOSS_JID
    assert joburl.job_id("https://boards.greenhouse.io/stripe/jobs/4321") == "4321"
    assert joburl.job_id("https://jobs.ashbyhq.com/duna/8e5d65f5-3487-442a-ba47-3983e0d54b51") \
        == "8e5d65f5-3487-442a-ba47-3983e0d54b51"


# ---- end to end, with a fake board ---------------------------------------------
def _ashby_board(jobs):
    return {"jobs": jobs}


def _job(jid, title):
    return {"id": jid, "title": title, "isListed": True, "descriptionPlain": "",
            "descriptionHtml": f"<p>{title} description</p>", "jobUrl": f"https://x/{jid}",
            "location": "Berlin", "department": "Product"}


def test_resolves_the_moss_embed_to_one_posting():
    calls = []

    def fake_fetch(url):
        calls.append(url)
        if "job-board/getmoss" in url:
            raise RuntimeError("404")          # first guess misses, as it does live
        if "job-board/moss" in url:
            return _ashby_board([_job(MOSS_JID, "Senior Product Manager"),
                                 _job("other-id", "Product Systems & AI Automation Specialist")])
        raise AssertionError("unexpected " + url)

    job, err = joburl.fetch_posting(MOSS_EMBED, fetcher=fake_fetch)
    assert err is None, err
    assert job["title"] == "Senior Product Manager"
    assert job["description"], "description must carry the posting text"
    assert len(calls) == 2, "should fall through the failed guess to the next one"


def test_wrong_id_refuses_rather_than_returning_a_neighbour():
    # The dangerous failure: two roles at the same company, wrong one silently returned.
    def fake_fetch(url):
        return _ashby_board([_job("aaa", "Senior Product Manager"),
                             _job("bbb", "Product Systems & AI Automation Specialist")])

    job, err = joburl.fetch_posting(
        "https://www.getmoss.com/careers?ashby_jid=not-a-real-id", fetcher=fake_fetch)
    assert job is None
    assert "no posting matching" in err


def test_no_id_and_many_roles_refuses():
    def fake_fetch(url):
        return _ashby_board([_job("aaa", "A"), _job("bbb", "B")])

    job, err = joburl.fetch_posting("https://jobs.ashbyhq.com/moss/", fetcher=fake_fetch)
    assert job is None, "must not guess which of several roles was meant"


def test_no_id_and_one_role_is_unambiguous():
    def fake_fetch(url):
        return _ashby_board([_job("only", "Senior Product Manager")])

    job, err = joburl.fetch_posting("https://jobs.ashbyhq.com/moss/", fetcher=fake_fetch)
    assert err is None and job["title"] == "Senior Product Manager"


def test_non_ats_url_explains_itself():
    job, err = joburl.fetch_posting("https://example.com/careers")
    assert job is None
    assert "Paste the posting text instead" in err


def test_cli_runs_as_a_bare_script_and_as_a_module():
    """
    Regression: joburl.py used a relative import, so `python scout/joburl.py <url>` died
    with ImportError even though every logic test passed. That invocation is the one
    written into cv-tailor's SKILL.md, i.e. the only one a user ever types. Logic tests
    import the module and so could never have caught it.
    """
    import subprocess

    root = Path(__file__).parents[1]
    for argv in (["python3", "scout/joburl.py", "https://example.com/careers"],
                 ["python3", "-m", "scout.joburl", "https://example.com/careers"]):
        p = subprocess.run(argv, cwd=root, capture_output=True, text=True)
        assert "ImportError" not in p.stderr, f"{argv} -> {p.stderr}"
        assert p.returncode == 1, f"{argv} should exit 1 on an unresolvable link"
        assert "Paste the posting text instead" in p.stderr


def test_every_board_failing_reports_what_was_tried():
    def fake_fetch(url):
        raise RuntimeError("HTTP 404")

    job, err = joburl.fetch_posting(MOSS_EMBED, fetcher=fake_fetch)
    assert job is None
    assert "getmoss" in err and "moss" in err


if __name__ == "__main__":
    import traceback
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); passed += 1
            except Exception:
                failed += 1
                print(f"FAIL {name}"); traceback.print_exc()
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
