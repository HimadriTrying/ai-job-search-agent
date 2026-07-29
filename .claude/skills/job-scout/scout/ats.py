"""
ats.py — keyless public-JSON clients for the four ATS platforms, normalized to one schema.

Companies are addressed as "ats:token", e.g. "greenhouse:stripe", "lever:palantir",
"ashby:ramp", "smartrecruiters:Company". Endpoints verified as current public JSON feeds
(no auth, no key). Slugs can drift; a renamed board 404s or returns empty — update the
watchlist when that happens.

NOTE: the live fetch needs network access; it is intentionally isolated in `fetch_json` so the
pure normalization logic can be unit-tested offline against fixtures.
"""

from __future__ import annotations
import json
import socket
import urllib.request
import urllib.error

UA = {"User-Agent": "job-scout/0.1 (personal job search)"}
TIMEOUT = 20


class FetchError:
    """A failed watchlist fetch, carrying *why* it failed as well as what to print.

    The kind matters because the two common failures need opposite advice, and telling a
    user to fix their watchlist when their network is blocked sends them to edit a file
    that was never the problem:
      "network" — no route to the ATS at all (blocked proxy, VPN, DNS, offline, timeout)
      "missing" — the ATS answered and said no such board (slug drift)
      "config"  — the watchlist line itself is malformed
      "other"   — reached the ATS, but something else went wrong (bad JSON, 5xx)
    Renders as its message so digest output stays a plain string.
    """

    __slots__ = ("kind", "message")

    def __init__(self, kind: str, message: str):
        self.kind = kind
        self.message = message

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:  # keeps test failures readable
        return f"FetchError({self.kind!r}, {self.message!r})"

    def __eq__(self, other):  # so tests can compare against the plain message
        return str(self) == str(other)


def classify_exception(exc: BaseException) -> str:
    """Map a fetch exception to a FetchError kind.

    URLError wraps the real cause in .reason, which is where a blocked proxy shows up
    (the tunnel-refused case is what a corporate network or a restricted container
    actually produces, and it is otherwise indistinguishable from a dead slug).
    """
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in (404, 410):
            return "missing"
        if exc.code in (403, 407):
            # A proxy denying CONNECT surfaces as 403/407 from the tunnel, not the ATS.
            return "network"
        return "other"
    if isinstance(exc, (urllib.error.URLError, socket.timeout, TimeoutError, OSError)):
        reason = getattr(exc, "reason", exc)
        text = str(reason).lower()
        if "tunnel" in text or "proxy" in text or "forbidden" in text:
            return "network"
        if isinstance(reason, (socket.gaierror, socket.timeout, TimeoutError, ConnectionError)):
            return "network"
        if any(s in text for s in ("timed out", "name or service", "unreachable",
                                   "connection refused", "temporary failure", "ssl")):
            return "network"
        return "network"
    return "other"

ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{token}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true",
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{token}/postings",
}

# SmartRecruiters list results carry no description; full text needs a per-posting call.
SR_POSTING = "https://api.smartrecruiters.com/v1/companies/{token}/postings/{id}"


def fetch_json(url: str):
    """Live GET returning parsed JSON. Raises on network/HTTP error (caller handles)."""
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---- Normalizers: raw ATS payload -> list of unified job dicts ------------------
def _norm_greenhouse(data: dict, company: str) -> list[dict]:
    out = []
    for j in data.get("jobs", []):
        out.append({
            "id": str(j.get("id")),
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name", ""),
            "department": ", ".join(d.get("name", "") for d in j.get("departments", []) or []),
            "url": j.get("absolute_url", ""),
            "description": j.get("content", "") or "",
            "comp_max": None,
            "source": "greenhouse", "company": company,
        })
    return out


def _norm_lever(data: list, company: str) -> list[dict]:
    out = []
    for j in data or []:
        cats = j.get("categories", {}) or {}
        out.append({
            "id": str(j.get("id", "")),
            "title": j.get("text", ""),
            "location": cats.get("location", ""),
            "department": cats.get("team", "") or cats.get("department", ""),
            "url": j.get("hostedUrl", ""),
            "description": j.get("descriptionPlain", "") or j.get("description", "") or "",
            "comp_max": None,
            "source": "lever", "company": company,
        })
    return out


def _norm_ashby(data: dict, company: str) -> list[dict]:
    out = []
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        comp_max = None
        comp = j.get("compensation") or {}
        # Ashby comp shape varies; pull an upper bound if present.
        for tier in comp.get("compensationTiers", []) or []:
            for c in tier.get("components", []) or []:
                mx = c.get("maxValue")
                if isinstance(mx, (int, float)):
                    comp_max = max(comp_max or 0, int(mx))
        out.append({
            "id": str(j.get("id", "")),
            "title": j.get("title", ""),
            "location": j.get("location", "") or j.get("locationName", ""),
            "department": j.get("department", "") or j.get("team", ""),
            "url": j.get("jobUrl", "") or j.get("applyUrl", ""),
            "description": j.get("descriptionPlain", "") or j.get("descriptionHtml", "") or "",
            "comp_max": comp_max,
            "source": "ashby", "company": company,
        })
    return out


def _norm_smartrecruiters(data: dict, company: str) -> list[dict]:
    out = []
    for j in data.get("content", []):
        loc = j.get("location", {}) or {}
        out.append({
            "id": str(j.get("id", "")),
            "title": j.get("name", ""),
            "location": ", ".join(x for x in [loc.get("city"), loc.get("country")] if x),
            "department": (j.get("department") or {}).get("label", ""),
            "url": j.get("ref", "") or f"https://jobs.smartrecruiters.com/{company}/{j.get('id','')}",
            "description": "",  # SR needs a per-posting call for full text; keep the sweep cheap
            "comp_max": None,
            "source": "smartrecruiters", "company": company,
        })
    return out


def sr_description_from_posting(data: dict) -> str:
    """Extract the full text from a SmartRecruiters posting-detail payload.
    Pure parsing, unit-testable offline."""
    sections = (data.get("jobAd") or {}).get("sections") or {}
    parts = []
    for key in ("companyDescription", "jobDescription", "qualifications", "additionalInformation"):
        sec = sections.get(key) or {}
        if sec.get("text"):
            parts.append(sec["text"])
    return "\n".join(parts)


def fetch_sr_description(company: str, posting_id: str) -> str:
    """Live detail fetch; returns '' on any failure so one missing posting never
    crashes the sweep (the caller records how many came back empty)."""
    try:
        return sr_description_from_posting(
            fetch_json(SR_POSTING.format(token=company, id=posting_id)))
    except Exception:  # noqa: BLE001 - deliberately broad; degraded, not fatal
        return ""


_NORMALIZERS = {
    "greenhouse": _norm_greenhouse,
    "lever": _norm_lever,
    "ashby": _norm_ashby,
    "smartrecruiters": _norm_smartrecruiters,
}


def normalize(ats: str, raw, company: str) -> list[dict]:
    return _NORMALIZERS[ats](raw, company)


def fetch_company(entry: str) -> tuple[list[dict], str | None]:
    """
    entry: 'ats:token'. Returns (jobs, error). On any failure returns ([], reason) so one
    dead slug never crashes the whole sweep.
    """
    try:
        ats, token = entry.split(":", 1)
    except ValueError:
        return [], FetchError("config", f"bad watchlist entry (need ats:token): {entry!r}")
    if ats not in ENDPOINTS:
        return [], FetchError("config", f"unknown ATS '{ats}' in {entry!r}")
    url = ENDPOINTS[ats].format(token=token)
    try:
        raw = fetch_json(url)
    except urllib.error.HTTPError as e:
        kind = classify_exception(e)
        hint = ("blocked before reaching the ATS" if kind == "network"
                else "slug drift? board moved ATS?")
        return [], FetchError(kind, f"{entry}: HTTP {e.code} ({hint})")
    except Exception as e:  # noqa: BLE001 - deliberately broad; log and continue
        return [], FetchError(classify_exception(e), f"{entry}: {type(e).__name__}: {e}")
    return normalize(ats, raw, token), None
