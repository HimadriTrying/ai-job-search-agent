"""
Offline tests for the correction loop's rule store. No network, fictional data only.
Run:  python scripts/tests/test_learned_rules.py    (or python -m pytest -q)

These are mutation tests, and that is deliberate. Two of the checks in
scripts/check-cover-letter.sh would have shipped silently inert if they had only ever been
run against a document that passed. A checker nobody has watched fail is not known to work,
so every check here is proved twice: once on a document that should pass, and once on a
document mutated to break exactly that rule.

The contract they encode:
  - an empty or missing store passes everything (a new user is not punished for being new)
  - a `forbid` rule fires on the banned text and stays quiet otherwise
  - a `require` rule fires on absence and stays quiet on presence
  - scope is honoured: a letter rule does not fire on a CV
  - `all` scope fires on every document type
  - prose-only rules never fail a check, but do appear in the drafter's brief
  - a broken regex is reported, not silently skipped
  - `add` refuses a duplicate id and refuses an invalid rule
  - `add` preserves the explanatory header the user's own file carries
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import learned_rules as lr


def store_with(rules_yaml: str, tmp: Path, header: str = "") -> Path:
    path = tmp / "learned-rules.yaml"
    path.write_text(header + rules_yaml, encoding="utf-8")
    return path


def doc_with(text: str, tmp: Path, name: str = "draft.md") -> Path:
    path = tmp / name
    path.write_text(text, encoding="utf-8")
    return path


def run_check(store: Path, doc: Path, scope=None) -> int:
    argv = ["--store", str(store), "check", str(doc)]
    if scope:
        argv += ["--scope", scope]
    return lr.main(argv)


FORBID_STORE = """
rules:
  - id: no-passionate
    added: 2026-08-21
    scope: [letter]
    rule: Never describe yourself as passionate about anything.
    check:
      type: forbid
      pattern: '\\bpassionate\\b'
      message: banned register
"""

REQUIRE_STORE = """
rules:
  - id: must-sign-off
    added: 2026-08-21
    scope: [letter]
    rule: Every letter ends with a sign-off.
    check:
      type: require
      pattern: '(Best regards|Kind regards)'
      message: no sign-off found
"""


def test_missing_store_passes():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = doc_with("Anything at all, passionate included.", tmp)
        assert run_check(tmp / "does-not-exist.yaml", doc) == 0


def test_empty_store_passes():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with("rules: []\n", tmp)
        doc = doc_with("I am passionate about everything.", tmp)
        assert run_check(store, doc) == 0


def test_forbid_fires_on_the_banned_text():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with(FORBID_STORE, tmp)
        doc = doc_with("I am passionate about payments infrastructure.", tmp)
        assert run_check(store, doc, "letter") == 1


def test_forbid_is_quiet_on_a_clean_document():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with(FORBID_STORE, tmp)
        doc = doc_with("I spent four years on payments infrastructure.", tmp)
        assert run_check(store, doc, "letter") == 0


def test_forbid_does_not_overshoot_a_legitimate_neighbour():
    """Widening a rule must not catch the words next to the one that got corrected."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with(FORBID_STORE, tmp)
        doc = doc_with("The team's compassion for its users was the reason it worked.", tmp)
        assert run_check(store, doc, "letter") == 0


def test_require_fires_on_absence():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with(REQUIRE_STORE, tmp)
        doc = doc_with("Dear team, here is my letter. Himadri", tmp)
        assert run_check(store, doc, "letter") == 1


def test_require_is_quiet_on_presence():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with(REQUIRE_STORE, tmp)
        doc = doc_with("Dear team, here is my letter.\n\nBest regards,\nHimadri", tmp)
        assert run_check(store, doc, "letter") == 0


def test_scope_is_honoured():
    """A letter rule must not fire on a CV. Scope is what keeps the store from becoming noise."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with(FORBID_STORE, tmp)
        doc = doc_with("Passionate about payments.", tmp)
        assert run_check(store, doc, "cv") == 0
        assert run_check(store, doc, "letter") == 1


def test_scope_all_fires_everywhere():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with(FORBID_STORE.replace("[letter]", "[all]"), tmp)
        doc = doc_with("Passionate about payments.", tmp)
        assert run_check(store, doc, "cv") == 1
        assert run_check(store, doc, "outreach") == 1


def test_prose_only_rule_never_fails_a_check_but_reaches_the_brief(capsys=None):
    """Most corrections have no mechanical form. They must still reach the drafter."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with(
            "rules:\n"
            "  - id: lead-with-the-outcome\n"
            "    added: 2026-08-21\n"
            "    scope: [cv]\n"
            "    rule: Lead every bullet with the outcome, not the activity.\n"
            "    why: Corrected twice on the same draft.\n",
            tmp,
        )
        doc = doc_with("Managed a team and shipped some things.", tmp)
        assert run_check(store, doc, "cv") == 0

        rules = lr.load_store(store)
        assert len(rules) == 1
        assert lr.applies_to(rules[0], "cv")
        assert not lr.applies_to(rules[0], "letter")


def test_broken_regex_is_reported_not_skipped():
    """A rule that cannot run is a rule the user thinks is protecting them. Say so."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with(
            "rules:\n"
            "  - id: broken\n"
            "    added: 2026-08-21\n"
            "    scope: [all]\n"
            "    rule: Something.\n"
            "    check:\n"
            "      type: forbid\n"
            "      pattern: '([unclosed'\n",
            tmp,
        )
        doc = doc_with("Harmless text.", tmp)
        assert run_check(store, doc) == 1


def test_validate_catches_a_malformed_store():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with(
            "rules:\n"
            "  - id: Bad_ID\n"
            "    scope: [nonsense]\n",
            tmp,
        )
        problems = lr.validate_rules(lr.load_store(store))
        joined = " ".join(problems)
        assert "kebab-case" in joined
        assert "unknown scope" in joined
        assert "missing required field 'rule'" in joined


def test_add_writes_a_rule_and_refuses_a_duplicate():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = tmp / "learned-rules.yaml"
        argv = [
            "--store", str(store), "add",
            "--id", "no-passionate",
            "--scope", "letter,cv",
            "--rule", "Never say passionate.",
            "--why", "Said so on 21 Aug.",
            "--pattern", r"\bpassionate\b",
        ]
        assert lr.main(argv) == 0
        rules = lr.load_store(store)
        assert rules[0]["id"] == "no-passionate"
        assert rules[0]["check"]["type"] == "forbid"
        assert set(rules[0]["scope"]) == {"letter", "cv"}
        # And it is live immediately, not on the next session.
        doc = doc_with("I am passionate.", tmp)
        assert run_check(store, doc, "letter") == 1
        # A second add under the same id must refuse rather than silently overwrite.
        assert lr.main(argv) == 2


def test_add_refuses_an_invalid_regex():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = tmp / "learned-rules.yaml"
        assert lr.main([
            "--store", str(store), "add",
            "--id", "bad-regex",
            "--scope", "all",
            "--rule", "Something.",
            "--pattern", "([unclosed",
        ]) == 2
        assert not store.exists()


def test_add_preserves_the_users_header():
    """The store ships with an explanation. Writing a rule must not eat it."""
    header = "# My rules. Delete anything here you disagree with.\n\n"
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        store = store_with("rules: []\n", tmp, header=header)
        assert lr.main([
            "--store", str(store), "add",
            "--id", "first-rule",
            "--scope", "all",
            "--rule", "Say the thing plainly.",
        ]) == 0
        text = store.read_text(encoding="utf-8")
        assert text.startswith(header)
        assert "first-rule" in text


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
    print("all learned-rule tests passed" if not failures else f"{failures} test(s) failed")
    sys.exit(1 if failures else 0)
