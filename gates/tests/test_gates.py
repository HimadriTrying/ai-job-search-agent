"""
Offline tests for the gate runner and the session ledger. No network, fictional data only.
Run:  python gates/tests/test_gates.py    (or python -m pytest -q)

Mutation tests again, for the same reason: a gate nobody has watched fire is not known to work,
and a gate nobody has watched STAY QUIET is worse, because a gate that fires on a README teaches
the user to switch the whole thing off.

The contract:
  - drafts under applications/ are classified by kind; repo prose is never classified
  - the classifier is conservative about both directory and file extension
  - a missing career_facts.yaml SKIPS the honesty gate rather than blocking a new user
  - the ledger reports a draft that failed, and one written but never passed
  - a draft that passed its checks but was never READ is still unfinished
  - a review receipt with no findings is refused, and editing a draft invalidates its review
  - storing a rule resolves a noticed correction on its own, with nothing else to run
  - an explicit one-off also resolves it
  - after MAX_BLOCKS the ledger stops blocking and reports instead
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "gates"))

import run as gates
import session as ledger


# ------------------------------------------------------------------ classification

def test_letters_and_cvs_under_applications_are_gated():
    assert gates.classify(ROOT / "applications/moss/cover-moss.md") == "letter"
    assert gates.classify(ROOT / "applications/moss/Himadri_CV_Moss.md") == "cv"
    assert gates.classify(ROOT / "applications/moss/resume.html") == "cv"
    assert gates.classify(ROOT / "data/drafts/outreach-jane.md") == "outreach"


def test_repo_prose_is_never_gated():
    """The commonest way to get a guard switched off is to have it fire on the wrong thing."""
    for p in ("README.md", "CLAUDE.md", "docs/DESIGN.md", "docs/FAILURE-MODES.md",
              "profile/00-README.md", "profile/06-cover-letter-notes.example.md",
              "ROADMAP.md", "honesty/README.md"):
        assert gates.classify(ROOT / p) is None, f"{p} must not be gated"


def test_directory_and_extension_are_both_required():
    # Right name, wrong place.
    assert gates.classify(ROOT / "notes/cover-letter-ideas.md") is None
    # Right place, wrong extension.
    assert gates.classify(ROOT / "applications/moss/cover-moss.pdf") is None
    # Right place, no recognisable kind.
    assert gates.classify(ROOT / "applications/moss/README.md") is None


def test_company_is_read_from_the_parent_directory():
    assert gates.company_from(Path("applications/moss/cover-moss.md")) == "moss"
    assert gates.company_from(Path("applications/cover.md")) == ""


# ------------------------------------------------------------------ graceful skips

def test_honesty_skips_without_frozen_facts_rather_than_blocking():
    """A half-set-up user must not be locked out of their own drafts by their own guard."""
    with tempfile.TemporaryDirectory() as d:
        doc = Path(d) / "cover-x.md"
        doc.write_text("Dear team, hello.", encoding="utf-8")
        result = gates.gate_honesty(doc)
        if not (ROOT / "career_facts.yaml").exists():
            assert result.status == "skip"
            assert not result.blocking
            assert "setup" in result.message


def test_missing_file_is_not_a_failure():
    assert gates.main(["/nonexistent/path/cover-nothing.md"]) == 0


# ------------------------------------------------------------------ the ledger

def fresh(session: str):
    p = ledger.ledger_path(session)
    if p.exists():
        p.unlink()


def test_ledger_reports_a_failed_draft():
    s = "test-failed-draft"
    fresh(s)
    ledger.main(["record", "--session", s, "--event", "draft-failed",
                 "--path", "applications/x/cover-x.md", "--note", "no research"])
    items = ledger.open_items(ledger.load(s))
    assert len(items) == 1 and "cover-x.md" in items[0] and "no research" in items[0]
    fresh(s)


def test_ledger_reports_a_draft_written_but_never_passed():
    s = "test-written-only"
    fresh(s)
    ledger.main(["record", "--session", s, "--event", "draft-written",
                 "--path", "applications/x/cover-x.md"])
    assert "never passed" in ledger.open_items(ledger.load(s))[0]
    fresh(s)


def _draft(tmp, text="A draft that passes its mechanical checks.\n"):
    p = Path(tmp) / "cover-x.md"
    p.write_text(text, encoding="utf-8")
    return str(p)


FINDINGS = ("Two flagships at equal weight in beat 2; the closer would be true of any "
            "competitor; the opening explains the company to itself.")


def test_passing_the_checks_is_not_being_finished():
    """Mechanical checks bound the floor. The faults that cost the most rounds are the ones no
    script can see, so a draft nothing has READ is still unfinished."""
    s = "test-passed"
    fresh(s)
    with tempfile.TemporaryDirectory() as d:
        doc = _draft(d)
        ledger.main(["record", "--session", s, "--event", "draft-passed", "--path", doc])
        items = ledger.open_items(ledger.load(s))
        assert len(items) == 1 and "no Reviewer has read it" in items[0]
    fresh(s)


def test_a_reviewed_draft_leaves_nothing_open():
    s = "test-reviewed"
    fresh(s)
    with tempfile.TemporaryDirectory() as d:
        doc = _draft(d)
        ledger.main(["record", "--session", s, "--event", "draft-passed", "--path", doc])
        ledger.main(["record", "--session", s, "--event", "draft-reviewed",
                     "--path", doc, "--note", FINDINGS])
        assert ledger.open_items(ledger.load(s)) == []
    fresh(s)


def test_a_receipt_without_findings_is_refused():
    """A checkmark is not a critique. This cannot prove the Reviewer ran; it does mean nobody
    can call a draft finished while nothing at all has been filed."""
    s = "test-thin-receipt"
    fresh(s)
    with tempfile.TemporaryDirectory() as d:
        doc = _draft(d)
        ledger.main(["record", "--session", s, "--event", "draft-passed", "--path", doc])
        assert ledger.main(["record", "--session", s, "--event", "draft-reviewed",
                            "--path", doc, "--note", "looks good"]) == 2
        assert ledger.main(["record", "--session", s, "--event", "draft-reviewed",
                            "--path", doc]) == 2
        assert "no Reviewer has read it" in ledger.open_items(ledger.load(s))[0]
    fresh(s)


def test_editing_a_draft_invalidates_its_review():
    """The Reviewer is only useful on the text that will actually be sent. Without this, a
    draft could be reviewed once and then rewritten five times behind the receipt."""
    s = "test-stale-review"
    fresh(s)
    with tempfile.TemporaryDirectory() as d:
        doc = _draft(d)
        ledger.main(["record", "--session", s, "--event", "draft-passed", "--path", doc])
        ledger.main(["record", "--session", s, "--event", "draft-reviewed",
                     "--path", doc, "--note", FINDINGS])
        assert ledger.open_items(ledger.load(s)) == []

        Path(doc).write_text("Rewritten from scratch after the review.\n", encoding="utf-8")
        items = ledger.open_items(ledger.load(s))
        assert len(items) == 1 and "changed after it was reviewed" in items[0]
    fresh(s)


def test_an_unresolved_correction_stays_open():
    s = "test-correction"
    fresh(s)
    ledger.main(["record", "--session", s, "--event", "correction-noticed"])
    items = ledger.open_items(ledger.load(s))
    assert len(items) == 1 and "never resolved" in items[0]
    fresh(s)


def test_storing_a_rule_resolves_it_by_itself(monkeypatch=None):
    """Storing the rule IS the resolution. Requiring a second command to say so would be one
    more step the model could skip, which is the failure this machinery exists to remove."""
    s = "test-autoresolve"
    fresh(s)
    counts = iter([2, 3])          # 2 rules when noticed, 3 by the time we check
    real = ledger.rule_count
    ledger.rule_count = lambda: next(counts)
    try:
        ledger.main(["record", "--session", s, "--event", "correction-noticed"])
        assert ledger.open_items(ledger.load(s)) == []
    finally:
        ledger.rule_count = real
        fresh(s)


def test_an_explicit_one_off_also_resolves_it():
    s = "test-oneoff"
    fresh(s)
    ledger.main(["record", "--session", s, "--event", "correction-noticed"])
    ledger.main(["record", "--session", s, "--event", "correction-resolved",
                 "--note", "one-off"])
    assert ledger.open_items(ledger.load(s)) == []
    fresh(s)


def test_it_stops_blocking_after_max_blocks():
    """A gate that can never be satisfied is worse than one that can be skipped: it burns quota
    in a loop the user did not ask for and cannot see."""
    s = "test-maxblocks"
    fresh(s)
    ledger.main(["record", "--session", s, "--event", "draft-failed",
                 "--path", "applications/x/cover-x.md"])
    assert ledger.main(["open-items", "--session", s]) == 1
    for _ in range(ledger.MAX_BLOCKS):
        ledger.main(["record", "--session", s, "--event", "blocked"])
    assert ledger.main(["open-items", "--session", s]) == 0   # reports, does not block
    fresh(s)


def test_a_corrupt_ledger_does_not_break_the_session():
    s = "test-corrupt"
    ledger.ledger_path(s).write_text("{not json", encoding="utf-8")
    data = ledger.load(s)
    assert data["drafts"] == {} and data["corrections"]["noticed"] == 0
    fresh(s)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok    {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}  {exc}")
    print()
    print("all gate tests passed" if not failures else f"{failures} test(s) failed")
    sys.exit(1 if failures else 0)
