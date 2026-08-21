#!/usr/bin/env python3
"""
learned_rules.py — the store behind the correction loop.

WHY THIS EXISTS

A correction the user makes on a draft used to fix that draft and then die with the session,
so the same correction arrived again the following week. That looks like the agent forgetting.
It is not: the rule was never written anywhere it would be read again.

This is the anywhere. `profile/learned-rules.yaml` holds the rules the user has actually
stated, and this script is the two things that make the file load-bearing rather than
decorative:

    brief   — what the drafter reads BEFORE writing, so the rule is honoured
    check   — what the checker runs AFTER writing, so the rule is enforced

Both matter, and for different reasons. Only reading the rules means they get followed most
of the time. Only checking them means the model writes the wrong thing and then patches it.
Doing both is what makes a learned rule behave like a shipped one.

Usage:
    python scripts/learned_rules.py brief   [--scope letter] [--store PATH]
    python scripts/learned_rules.py check   <document> [--scope letter] [--store PATH]
    python scripts/learned_rules.py add     --id ID --scope letter --rule "..." [...]
    python scripts/learned_rules.py list    [--scope letter]
    python scripts/learned_rules.py validate

Exit codes:
    0  = clean / nothing to report
    1  = a learned rule was violated (check), or the store is invalid (validate)
    2  = usage or file error

DESIGN NOTES

*Only the user's own rules live here.* A rule that would be true for any user of Lucy belongs
in the shipped house spec, not in one person's store. The `add` path is deliberately explicit
about which it is: the `learn` skill asks before writing anything.

*Mechanical where possible, prose where not.* A rule with a `check:` block is enforced; one
without is still printed into the drafter's brief. Most real corrections start as prose and
only some of them can be made mechanical, so the file has to hold both or it will hold
neither.

*Nothing is inferred.* Entries arrive only when the user has said the rule should stand. The
file is plain YAML the user can read, edit and delete; legible learning or no learning.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("Missing dependency: pip install pyyaml\n")
    sys.exit(2)

DEFAULT_STORE = "profile/learned-rules.yaml"
VALID_SCOPES = ("cv", "letter", "outreach", "all")
VALID_CHECK_TYPES = ("forbid", "require")

# A document big enough to hang a pathological regex is not a document anyone is drafting.
MAX_DOC_BYTES = 2_000_000

# Rules in one scope, above which the brief starts costing more context than it saves.
CONSOLIDATE_ABOVE = 25


# --------------------------------------------------------------------------- loading


def load_store(path: Path) -> list[dict]:
    """Read the store. A missing store is not an error: it means nothing is learned yet."""
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        sys.stderr.write(f"{path} is not valid YAML: {exc}\n")
        sys.exit(2)
    if not isinstance(data, dict):
        sys.stderr.write(f"{path} must be a mapping with a top-level 'rules:' key.\n")
        sys.exit(2)
    rules = data.get("rules") or []
    if not isinstance(rules, list):
        sys.stderr.write(f"{path}: 'rules' must be a list.\n")
        sys.exit(2)
    return [r for r in rules if isinstance(r, dict)]


def validate_rules(rules: list[dict]) -> list[str]:
    """Return a list of problems. Empty list means the store is well formed."""
    problems: list[str] = []
    seen_ids: set[str] = set()

    for i, rule in enumerate(rules):
        where = rule.get("id") or f"entry {i + 1}"

        for field in ("id", "scope", "rule"):
            if not rule.get(field):
                problems.append(f"{where}: missing required field '{field}'")

        rid = rule.get("id")
        if rid:
            if not isinstance(rid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", rid):
                problems.append(f"{where}: id must be lowercase kebab-case")
            elif rid in seen_ids:
                problems.append(f"{where}: duplicate id")
            else:
                seen_ids.add(rid)

        scopes = normalise_scope(rule.get("scope"))
        for scope in scopes:
            if scope not in VALID_SCOPES:
                problems.append(f"{where}: unknown scope '{scope}' (use {', '.join(VALID_SCOPES)})")

        check = rule.get("check")
        if check is not None:
            if not isinstance(check, dict):
                problems.append(f"{where}: 'check' must be a mapping")
                continue
            ctype = check.get("type")
            if ctype not in VALID_CHECK_TYPES:
                problems.append(
                    f"{where}: check.type must be one of {', '.join(VALID_CHECK_TYPES)}"
                )
            pattern = check.get("pattern")
            if not pattern:
                problems.append(f"{where}: check needs a 'pattern'")
            else:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    problems.append(f"{where}: check.pattern is not a valid regex ({exc})")

    return problems


def normalise_scope(scope) -> list[str]:
    """Scope may be written as a string or a list. Treat both the same."""
    if scope is None:
        return []
    if isinstance(scope, str):
        return [scope.strip()]
    if isinstance(scope, list):
        return [str(s).strip() for s in scope if str(s).strip()]
    return []


def applies_to(rule: dict, scope: str | None) -> bool:
    """No scope asked for means every rule. 'all' in a rule means it always applies."""
    if scope is None:
        return True
    scopes = normalise_scope(rule.get("scope"))
    return "all" in scopes or scope in scopes


# --------------------------------------------------------------------------- commands


def cmd_brief(args) -> int:
    """What the drafter reads before writing. Prose and mechanical rules alike.

    This runs before every draft, so its size is a recurring cost on the user's context, not
    a one-off. Two things keep it small:

    *Scope.* Only the rules governing the document being written are printed.

    *No `why` by default.* The reason a rule exists matters to the human deciding whether to
    retire it; the drafter only needs the instruction. Dropping it roughly halves the brief.
    `--why` puts it back when someone is auditing the store rather than drafting from it.
    """
    rules = [r for r in load_store(Path(args.store)) if applies_to(r, args.scope)]
    if not rules:
        return 0

    label = f" for this document type ({args.scope})" if args.scope else ""
    print(f"# Learned rules{label} — {len(rules)} the user has asked you to keep to")
    print(f"# Source: {args.store}. These are their rules, not the house spec.")
    print()
    for rule in rules:
        print(f"- {rule['rule']}".rstrip())
        if args.why and rule.get("why"):
            print(f"    (why: {rule['why']})")

    # A store that only ever grows becomes a memory test the model fails in a new shape each
    # week, and it is read before every draft, so it costs context every time. Past this many
    # rules in one scope, say so: the fix is consolidation or retirement, not a bigger brief.
    if len(rules) > CONSOLIDATE_ABOVE:
        print()
        print(f"# NOTE: {len(rules)} rules in this scope, above the {CONSOLIDATE_ABOVE} where a")
        print("# store starts costing more than it saves. Before adding another, offer to merge")
        print("# overlapping rules or retire ones that keep being overridden. A healthy set of")
        print("# rules gets shorter over time. See docs/FAILURE-MODES.md.")
    return 0


def cmd_check(args) -> int:
    """What the checker runs after writing. Only rules with a mechanical form fire here."""
    doc_path = Path(args.document)
    if not doc_path.exists():
        sys.stderr.write(f"No such document: {doc_path}\n")
        return 2
    if doc_path.stat().st_size > MAX_DOC_BYTES:
        sys.stderr.write(f"{doc_path} is too large to check ({doc_path.stat().st_size} bytes).\n")
        return 2

    text = doc_path.read_text(encoding="utf-8", errors="replace")
    rules = [r for r in load_store(Path(args.store)) if applies_to(r, args.scope)]
    checkable = [r for r in rules if isinstance(r.get("check"), dict)]

    failures: list[str] = []
    for rule in checkable:
        check = rule["check"]
        pattern, ctype = check.get("pattern"), check.get("type")
        if not pattern or ctype not in VALID_CHECK_TYPES:
            continue
        try:
            rx = re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            failures.append(f"[{rule['id']}] rule has a broken regex and could not run: {exc}")
            continue

        message = check.get("message") or rule["rule"]
        if ctype == "forbid":
            for m in rx.finditer(text):
                snippet = text[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")
                failures.append(f"[{rule['id']}] {message} — found '{m.group(0)}' near: ...{snippet}...")
                break  # one report per rule is enough to send it back
        elif ctype == "require" and not rx.search(text):
            failures.append(f"[{rule['id']}] {message} — required pattern never appears")

    if failures:
        print(f"FAIL  {doc_path}: {len(failures)} learned rule(s) violated")
        for f in failures:
            print(f"  {f}")
        print()
        print("These are rules you asked for, in " + args.store + ".")
        print("If one is wrong, edit or delete it there rather than working around it.")
        return 1

    prose_only = len(rules) - len(checkable)
    if not rules:
        print("learned rules: none stored yet")
    else:
        note = f", {prose_only} prose-only (not checkable here)" if prose_only else ""
        print(f"learned rules ok: {len(checkable)} check(s) passed{note}")
    return 0


def cmd_add(args) -> int:
    """Append one rule. The `learn` skill calls this after the user has confirmed the rule."""
    path = Path(args.store)
    rules = load_store(path)

    if any(r.get("id") == args.id for r in rules):
        sys.stderr.write(f"A rule with id '{args.id}' already exists in {path}. Edit it instead.\n")
        return 2

    entry: dict = {
        "id": args.id,
        "added": args.added or date.today().isoformat(),
        "scope": [s.strip() for s in args.scope.split(",") if s.strip()],
        "rule": args.rule,
    }
    if args.why:
        entry["why"] = args.why
    if args.rule_class:
        entry["class"] = args.rule_class
    if args.pattern:
        entry["check"] = {
            "type": args.check_type,
            "pattern": args.pattern,
            "message": args.message or args.rule,
        }

    problems = validate_rules(rules + [entry])
    if problems:
        sys.stderr.write("Refusing to write an invalid rule:\n")
        for p in problems:
            sys.stderr.write(f"  {p}\n")
        return 2

    rules.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)

    header = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        # Keep whatever explanatory header the user's file already carries.
        marker = existing.find("rules:")
        if marker > 0:
            header = existing[:marker]

    body = yaml.safe_dump({"rules": rules}, sort_keys=False, allow_unicode=True, width=95)
    path.write_text(header + body, encoding="utf-8")
    print(f"Learned: [{entry['id']}] {entry['rule']}")
    print(f"Written to {path}. Scope: {', '.join(entry['scope'])}.")
    if "check" in entry:
        print("It is mechanically checked, so it will fail the checker rather than be forgotten.")
    else:
        print("No mechanical form, so it is read by the drafter but cannot be checked.")
    return 0


def cmd_list(args) -> int:
    rules = [r for r in load_store(Path(args.store)) if applies_to(r, args.scope)]
    if not rules:
        print("No learned rules stored yet.")
        return 0
    for rule in rules:
        checked = "checked" if isinstance(rule.get("check"), dict) else "prose"
        scopes = ",".join(normalise_scope(rule.get("scope")))
        print(f"{rule.get('added', '?')}  [{rule.get('id')}]  ({scopes}, {checked})")
        print(f"    {rule.get('rule')}")
    return 0


def cmd_validate(args) -> int:
    path = Path(args.store)
    if not path.exists():
        print(f"{path} does not exist yet — nothing learned so far, which is valid.")
        return 0
    problems = validate_rules(load_store(path))
    if problems:
        print(f"FAIL  {path}: {len(problems)} problem(s)")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"{path} ok")
    return 0


# --------------------------------------------------------------------------- entry


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1], add_help=True)
    ap.add_argument("--store", default=DEFAULT_STORE, help=f"Rule store (default {DEFAULT_STORE})")
    sub = ap.add_subparsers(dest="command", required=True)

    p_brief = sub.add_parser("brief", help="Print the rules a drafter should read first.")
    p_brief.add_argument("--scope", choices=VALID_SCOPES[:-1], default=None)
    p_brief.add_argument("--why", action="store_true",
                         help="Include each rule's reason. Off by default: the drafter needs the "
                              "instruction, not the history, and this runs before every draft.")
    p_brief.set_defaults(func=cmd_brief)

    p_check = sub.add_parser("check", help="Enforce the mechanical rules against a document.")
    p_check.add_argument("document")
    p_check.add_argument("--scope", choices=VALID_SCOPES[:-1], default=None)
    p_check.set_defaults(func=cmd_check)

    p_add = sub.add_parser("add", help="Append a rule the user has confirmed should stand.")
    p_add.add_argument("--id", required=True)
    p_add.add_argument("--scope", required=True, help="Comma-separated: cv,letter,outreach,all")
    p_add.add_argument("--rule", required=True, help="One sentence, stated as an instruction.")
    p_add.add_argument("--why", help="What caused it. A rule with no remembered reason cannot be retired.")
    p_add.add_argument("--class", dest="rule_class", help="Failure class, see docs/FAILURE-MODES.md")
    p_add.add_argument("--added", help="ISO date; defaults to today.")
    p_add.add_argument("--pattern", help="Regex, if the rule has a mechanical form.")
    p_add.add_argument("--check-type", choices=VALID_CHECK_TYPES, default="forbid")
    p_add.add_argument("--message", help="What to print when the check fires.")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="Show everything learned so far.")
    p_list.add_argument("--scope", choices=VALID_SCOPES[:-1], default=None)
    p_list.set_defaults(func=cmd_list)

    p_validate = sub.add_parser("validate", help="Check the store itself is well formed.")
    p_validate.set_defaults(func=cmd_validate)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
