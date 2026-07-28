"""
joburl.py — turn ONE job-posting URL into the text of that posting.

Why this exists
---------------
Most startup job pages are an ATS board rendered client-side. `https://acme.com/careers`
serves a shell and JavaScript then injects the posting, so anything that fetches HTML
without running JS (an agent's web_fetch, curl, requests) gets a page with no job on it.
The old workaround was to ask the user to paste the whole posting by hand, which is the
single most cumbersome step in the whole funnel.

The fix is that the same four ATS platforms `ats.py` already sweeps also serve every
posting as public, keyless JSON. So instead of scraping the rendered page, resolve the URL
to its board's JSON feed and pick the one posting out of it.

This module is deliberately separate from `ats.py`: that one answers "what is open at this
company", addressed as `ats:token`. This one answers "what does THIS link say", addressed
as a URL a human pasted. It reuses `ats.ENDPOINTS` so there is one copy of each endpoint.

Two URL shapes, and the second is the awkward one:

  hosted   jobs.ashbyhq.com/moss/<uuid>        -> board token is in the path
  embedded www.getmoss.com/careers?ashby_jid=  -> board token is NOT in the URL at all

For embedded boards the token has to be guessed from the hostname, so `candidate_tokens`
returns several guesses in confidence order and `fetch_posting` tries them until a board
answers. `getmoss.com` resolves via the "strip a `get` prefix" guess, which is common
enough among B2B SaaS domains to be worth encoding.
"""

from __future__ import annotations

import re
import urllib.parse

try:
    from . import ats
except ImportError:  # run directly as a script: python scout/joburl.py <url>
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scout import ats

# Host fragments that identify a directly-hosted ATS board.
_HOSTED = {
    "ashbyhq.com": "ashby",
    "greenhouse.io": "greenhouse",
    "lever.co": "lever",
    "smartrecruiters.com": "smartrecruiters",
}

# Query parameters an embedded board uses to select one posting client-side. The presence
# of one of these is what tells us which ATS is behind a company's own careers page.
_EMBED_PARAMS = {
    "ashby_jid": "ashby",
    "gh_jid": "greenhouse",
    "gh_src": "greenhouse",
    "lever-jid": "lever",
}

# Subdomains that are the ATS product, not the customer's board token.
_NOT_A_TOKEN = {"jobs", "job-boards", "boards", "careers", "www", "api", "apply", "my"}

# Domain-name noise to strip when guessing a board token from a company hostname.
_STRIP_PREFIXES = ("get", "try", "use", "join", "the")
_STRIP_SUFFIXES = ("hq", "app", "inc", "io", "ai")


def _host_and_parts(url: str) -> tuple[str, list[str], dict]:
    parsed = urllib.parse.urlparse(url if "//" in url else "https://" + url)
    host = (parsed.netloc or "").lower().split(":")[0]
    parts = [p for p in (parsed.path or "").split("/") if p]
    query = urllib.parse.parse_qs(parsed.query or "")
    return host, parts, query


def detect_ats(url: str) -> str | None:
    """Which ATS is behind this URL, if any. Hosted boards win over embed hints."""
    host, _, query = _host_and_parts(url)
    for fragment, name in _HOSTED.items():
        if host == fragment or host.endswith("." + fragment):
            return name
    for param, name in _EMBED_PARAMS.items():
        if param in query:
            return name
    return None


def candidate_tokens(url: str) -> list[str]:
    """
    Board tokens to try, best guess first.

    For a hosted board the token is the first path segment and is the only candidate.
    For an embedded board nothing in the URL states it, so guess from the registered
    domain: the bare name, then the name with a common prefix or suffix stripped.
    """
    host, parts, _ = _host_and_parts(url)
    ats_name = detect_ats(url)

    hosted = any(host == f or host.endswith("." + f) for f in _HOSTED)
    if hosted:
        # smartrecruiters puts the company in the subdomain on some boards
        if parts and parts[0] not in _NOT_A_TOKEN:
            return [parts[0]]
        sub = host.split(".")[0]
        return [sub] if sub not in _NOT_A_TOKEN else []

    if ats_name is None:
        return []

    labels = [p for p in host.split(".") if p not in _NOT_A_TOKEN]
    if not labels:
        return []
    name = labels[0]

    out = [name]
    for prefix in _STRIP_PREFIXES:
        if name.startswith(prefix) and len(name) > len(prefix) + 2:
            out.append(name[len(prefix):])
    for suffix in _STRIP_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix) + 2:
            out.append(name[: -len(suffix)])
    # de-duplicate, preserve order
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def job_id(url: str) -> str | None:
    """The posting's own id, from the embed query param or the last path segment."""
    _, parts, query = _host_and_parts(url)
    for param in _EMBED_PARAMS:
        if param in query and query[param] and query[param][0]:
            return query[param][0]
    if parts:
        last = parts[-1]
        if _UUID.fullmatch(last) or last.isdigit() or (len(last) > 6 and last != "jobs"):
            return last
    return None


def parse(url: str) -> dict | None:
    """Everything resolvable from the URL alone. None when it is not an ATS link."""
    name = detect_ats(url)
    if name is None:
        return None
    return {"ats": name, "tokens": candidate_tokens(url), "job_id": job_id(url), "url": url}


def select(jobs: list[dict], wanted_id: str | None) -> dict | None:
    """
    Pick one normalized job out of a board.

    Matches on id first, then on the id appearing in the job's own url, which covers
    boards that expose a different public id than the one in the pasted link. With no id
    at all a single-posting board is unambiguous; anything larger is not, so return None
    rather than guess a job the user did not ask for.
    """
    if wanted_id:
        for j in jobs:
            if j.get("id") == wanted_id:
                return j
        for j in jobs:
            if wanted_id in (j.get("url") or ""):
                return j
        return None
    return jobs[0] if len(jobs) == 1 else None


def fetch_posting(url: str, fetcher=None) -> tuple[dict | None, str | None]:
    """
    Resolve a pasted job URL to the one posting it points at.

    Returns (job, error). `job` is in `ats.py`'s normalized schema, so `job["description"]`
    is the posting text the tailor needs. `fetcher` is injected so the resolution logic can
    be tested without network.

    Every failure is a returned reason, never an exception: this runs in front of a human
    who pasted a link, and "why not" is more useful to them than a traceback.
    """
    fetch_json = fetcher or ats.fetch_json
    parsed = parse(url)
    if parsed is None:
        return None, (
            "not a recognised ATS link (Greenhouse, Lever, Ashby, SmartRecruiters). "
            "Paste the posting text instead."
        )
    if not parsed["tokens"]:
        return None, f"could not work out the {parsed['ats']} board name from {url!r}"

    tried = []
    for token in parsed["tokens"]:
        endpoint = ats.ENDPOINTS[parsed["ats"]].format(token=token)
        try:
            raw = fetch_json(endpoint)
        except Exception as e:  # noqa: BLE001 - a wrong guess is expected, try the next
            tried.append(f"{token} ({type(e).__name__})")
            continue
        jobs = ats.normalize(parsed["ats"], raw, token)
        if not jobs:
            tried.append(f"{token} (board empty)")
            continue
        job = select(jobs, parsed["job_id"])
        if job is None:
            return None, (
                f"found the {token} board ({len(jobs)} open roles) but no posting matching "
                f"id {parsed['job_id']!r}. The posting may have closed."
            )
        return job, None

    return None, f"no {parsed['ats']} board answered for: {', '.join(tried)}"


def _cli(argv: list[str]) -> int:
    """
    python scout/joburl.py <job-url> [outfile]      (or: python -m scout.joburl ...)

    Prints the posting as markdown, or writes it to outfile. Exit 1 with the reason on
    stderr when the link cannot be resolved, so a caller can fall back to asking for a
    paste without having to parse the output.
    """
    import sys

    if not argv:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print("usage: python -m scout.joburl <job-url> [outfile]", file=sys.stderr)
        return 2

    job, err = fetch_posting(argv[0])
    if err:
        print(f"could not read that link: {err}", file=sys.stderr)
        return 1

    body = (
        f"# {job['title']}\n\n"
        f"* Company: {job['company']}\n"
        f"* Location: {job['location']}\n"
        f"* Department: {job['department']}\n"
        f"* Source: {job['source']}\n"
        f"* URL: {job['url']}\n\n"
        f"{job['description']}\n"
    )
    if len(argv) > 1:
        with open(argv[1], "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"wrote {argv[1]} ({len(job['description'])} chars of posting text)")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(_cli(sys.argv[1:]))
