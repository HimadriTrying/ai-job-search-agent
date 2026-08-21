#!/usr/bin/env python3
"""
session.py — the per-session ledger the gates read and write.

WHY THIS EXISTS

Enforcement needs memory of what happened earlier in the same session. "Was this draft ever
checked?" and "did the user correct something without it being resolved?" are both questions
about the past, and a hook fires with no memory of anything but its own input.

So each session gets a small JSON ledger, keyed by session id, holding only what a gate needs
to decide: which drafts were written, whether each one last passed or failed its gates, whether
a correction was noticed, and whether that correction was resolved.

It lives in the OS temp directory, not the repo. It is scratch state about one conversation,
it must not be committed, and it must not survive as a mystery file if the session dies.

Usage (the hooks call these; a human rarely does):
    python gates/session.py record   --session ID --event draft-failed --path FILE
    python gates/session.py record   --session ID --event correction-noticed
    python gates/session.py record   --session ID --event correction-resolved --note "one-off"
    python gates/session.py open-items --session ID     # what is still unresolved
    python gates/session.py show     --session ID
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

EVENTS = (
    "draft-written",       # a document the gates care about was written
    "draft-passed",        # ...and its gates passed
    "draft-failed",        # ...and its gates failed
    "correction-noticed",  # the user said something that reads like a correction
    "correction-resolved", # ...and it was stored as a rule, or recorded as a one-off
    "blocked",             # a Stop hook refused to end the turn
)

# After this many refusals in one session, stop blocking and report instead. A gate that can
# never be satisfied is worse than one that can be skipped: it burns the user's quota in a
# loop they did not ask for and cannot see.
MAX_BLOCKS = 3


def rule_count() -> int:
    """How many rules the learned-rules store holds, counted without parsing YAML.

    This is how a correction gets resolved without anyone remembering to say so: storing a rule
    IS the resolution, so the ledger snapshots the count when a correction is noticed and
    compares it later. Making the model run a second "I resolved it" command would be one more
    step it could skip, which is the exact failure this whole mechanism exists to remove.
    """
    store = Path(__file__).resolve().parents[1] / "profile" / "learned-rules.yaml"
    if not store.exists():
        return 0
    try:
        return sum(1 for line in store.read_text(encoding="utf-8").splitlines()
                   if re.match(r"^\s*-\s+id:", line))
    except OSError:
        return 0


def ledger_path(session: str) -> Path:
    safe = "".join(c for c in session if c.isalnum() or c in "-_")[:64] or "nosession"
    return Path(tempfile.gettempdir()) / f"lucy-gates-{safe}.json"


def load(session: str) -> dict:
    p = ledger_path(session)
    if not p.exists():
        return {"drafts": {}, "corrections": {"noticed": 0, "resolved": 0}, "blocks": 0}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # A corrupt ledger must never break the session. Start clean.
        return {"drafts": {}, "corrections": {"noticed": 0, "resolved": 0}, "blocks": 0}


def save(session: str, data: dict) -> None:
    try:
        ledger_path(session).write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass  # Losing scratch state degrades enforcement; it must not break the session.


def cmd_record(args) -> int:
    data = load(args.session)
    ev = args.event

    if ev in ("draft-written", "draft-passed", "draft-failed"):
        if not args.path:
            sys.stderr.write(f"{ev} needs --path\n")
            return 2
        entry = data["drafts"].setdefault(args.path, {"status": "written"})
        entry["status"] = {"draft-written": "written",
                           "draft-passed": "passed",
                           "draft-failed": "failed"}[ev]
        if args.note:
            entry["note"] = args.note[:500]
    elif ev == "correction-noticed":
        data["corrections"]["noticed"] += 1
        # Snapshot the store, so a rule stored later counts as the resolution by itself.
        data["corrections"].setdefault("rules_at_notice", rule_count())
    elif ev == "correction-resolved":
        data["corrections"]["resolved"] += 1
        if args.note:
            data["corrections"]["last"] = args.note[:200]
    elif ev == "blocked":
        data["blocks"] += 1

    save(args.session, data)
    return 0


def open_items(data: dict) -> list[str]:
    """What is still unfinished. This is the whole decision a Stop hook has to make."""
    items = []

    for path, entry in sorted(data.get("drafts", {}).items()):
        if entry.get("status") == "failed":
            note = entry.get("note", "")
            items.append(f"{path} last failed its gates{': ' + note if note else ''}")
        elif entry.get("status") == "written":
            items.append(f"{path} was written but never passed its gates")

    c = data.get("corrections", {})
    # A rule stored since the correction was noticed resolves it, with nothing else to run.
    rules_added = max(0, rule_count() - c.get("rules_at_notice", 0))
    unresolved = c.get("noticed", 0) - c.get("resolved", 0) - rules_added
    if unresolved > 0:
        items.append(
            f"{unresolved} correction(s) noticed but never resolved: ask whether each is a "
            f"one-off or a standing rule, then either store it with `learned_rules.py add` or "
            f"record the one-off with `session.py record --event correction-resolved`"
        )
    return items


def cmd_open_items(args) -> int:
    data = load(args.session)
    items = open_items(data)
    if data.get("blocks", 0) >= MAX_BLOCKS:
        # Report, do not block. See MAX_BLOCKS.
        if items:
            print("STALLED " + " | ".join(items))
        return 0
    for i in items:
        print(i)
    return 1 if items else 0


def cmd_show(args) -> int:
    print(json.dumps(load(args.session), indent=2))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Per-session ledger for Lucy's gates.")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("record")
    p.add_argument("--session", required=True)
    p.add_argument("--event", required=True, choices=EVENTS)
    p.add_argument("--path")
    p.add_argument("--note")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("open-items")
    p.add_argument("--session", required=True)
    p.set_defaults(func=cmd_open_items)

    p = sub.add_parser("show")
    p.add_argument("--session", required=True)
    p.set_defaults(func=cmd_show)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
