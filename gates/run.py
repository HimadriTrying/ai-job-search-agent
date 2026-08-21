#!/usr/bin/env python3
"""
run.py — the gate runner. Lucy's own enforcement, independent of any harness.

WHY THIS IS A PROGRAM AND NOT A HOOK

The checks in this repo already exit non-zero. The weakness was never the checks; it was that
running them was a *step a model performs*. A step can be skipped, and a skipped step leaves no
trace, so a document nobody checked looks exactly like one that passed.

This module makes the check a consequence of writing rather than a step after it. Given a path,
it works out what kind of document it is, runs every gate that applies, and reports. The Claude
Code hook in .claude/hooks/gate-on-write.sh is a nine-line adapter that calls this. That split
is deliberate: hooks are Claude Code's affordance, and the day Lucy runs somewhere else (an API
loop, a scheduled job, a hosted version) the guarantees have to come with it. They live here.

Usage:
    python gates/run.py <document>              # run every applicable gate
    python gates/run.py <document> --quiet      # print only failures
    python gates/run.py --list                  # what kinds are recognised

Exit codes:
    0  = passed, or nothing here to gate
    1  = a blocking gate failed
    2  = usage error

WHAT DOES NOT BLOCK

A gate that *cannot run* is reported and does not block. A new user with no career_facts.yaml
yet, or no research file because they are deliberately writing without one, must not be locked
out of their own tool by machinery meant to protect them. Skips are printed so the reason is
visible rather than silent. Set LUCY_GATES_OFF=1 to disable entirely; it is an escape hatch,
and the runner says so on every run when it is set.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Only these extensions are ever documents we gate.
DOC_SUFFIXES = {".md", ".markdown", ".html", ".txt", ".tex"}

# Conservative on purpose. A false positive here fires gates on a README or a session log and
# teaches the user to switch the whole thing off, which costs more than the miss it prevents.
KIND_PATTERNS = (
    # Anchored on token boundaries, all three. An unanchored alternation looks harmless and
    # is not: "dm" matches inside "REAdMe", so an unanchored outreach pattern gated every
    # README in a company folder. Caught by gates/tests/test_gates.py, which is the whole
    # reason a widened pattern gets its legitimate neighbours pinned by a test.
    ("letter",   re.compile(r"(^|[-_/])(cover|letter|motivation)", re.I)),
    ("cv",       re.compile(r"(^|[-_/])(cv|resume|résumé)([-_.]|$)", re.I)),
    ("outreach", re.compile(r"(^|[-_/])(outreach|intro|referral|message|dm)([-_.]|$)", re.I)),
)

# A document only counts if it lives somewhere drafts live. Keeps the gates off the repo's own
# prose (docs/, profile/, README) which is not an outbound document about the candidate.
DRAFT_DIRS = ("applications", "data/drafts", "drafts", "outbox")


class Result:
    def __init__(self, gate: str, status: str, message: str = ""):
        self.gate, self.status, self.message = gate, status, message

    @property
    def blocking(self) -> bool:
        return self.status == "fail"

    def __str__(self) -> str:
        mark = {"pass": "ok  ", "fail": "FAIL", "skip": "skip"}[self.status]
        return f"  {mark} {self.gate}{': ' + self.message if self.message else ''}"


def classify(path: Path) -> str | None:
    """Which kind of outbound document is this, if any? None means 'not ours to gate'."""
    if path.suffix.lower() not in DOC_SUFFIXES:
        return None
    try:
        rel = path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        rel = path.as_posix()          # outside the repo: judge on the path we were given
    if not any(f"{d}/" in f"{rel}/" for d in DRAFT_DIRS):
        return None
    for kind, rx in KIND_PATTERNS:
        if rx.search(rel):
            return kind
    return None


def company_from(path: Path) -> str:
    """Same convention check-cover-letter.sh uses: the parent directory is the company."""
    parent = path.parent.name
    return parent if parent not in ("", ".", "applications", "drafts") else ""


def run(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=120)
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return 127, "command not found"
    except subprocess.TimeoutExpired:
        return 124, "timed out"


def gate_learned_rules(path: Path, kind: str) -> Result:
    script = REPO / "scripts" / "learned_rules.py"
    if not script.exists():
        return Result("learned-rules", "skip", "scripts/learned_rules.py missing")
    code, out = run([sys.executable, str(script), "check", str(path), "--scope", kind])
    if code == 0:
        return Result("learned-rules", "pass")
    return Result("learned-rules", "fail", _tail(out))


def gate_letter_style(path: Path) -> Result:
    script = REPO / "scripts" / "check-cover-letter.sh"
    if not script.exists():
        return Result("letter-style", "skip", "scripts/check-cover-letter.sh missing")
    cmd = ["bash", str(script), str(path)]
    company = company_from(path)
    if company:
        cmd += ["--company", company]
    code, out = run(cmd)
    if code == 0:
        return Result("letter-style", "pass")
    return Result("letter-style", "fail", _tail(out, only_failures=True))


def gate_honesty(path: Path) -> Result:
    verify = REPO / "honesty" / "verify.py"
    facts = REPO / "career_facts.yaml"
    if not verify.exists():
        return Result("honesty", "skip", "honesty/verify.py missing")
    if not facts.exists():
        # The frozen facts are what the gate checks against. Without them there is nothing to
        # verify, and blocking here would lock a half-set-up user out of their own drafts.
        return Result("honesty", "skip",
                      "career_facts.yaml not found: run `setup` before trusting any draft")
    cmd = [sys.executable, str(verify), str(path)]
    company = company_from(path)
    if company:
        cmd += ["--target", company]
    code, out = run(cmd)
    if code == 0:
        return Result("honesty", "pass")
    if code == 2:
        return Result("honesty", "skip", _tail(out))
    return Result("honesty", "fail", _tail(out))


def _tail(text: str, limit: int = 6, only_failures: bool = False) -> str:
    """Keep gate output small. It lands in the model's context on every failing write."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if only_failures:
        failing = [l for l in lines if l.startswith(("FAIL", "✗")) or " FAIL " in l]
        lines = failing or lines
    if len(lines) > limit:
        lines = lines[:limit] + [f"... and {len(lines) - limit} more"]
    return " | ".join(lines)


GATES_BY_KIND = {
    "letter":   [gate_letter_style, gate_honesty],
    "cv":       [gate_honesty],
    "outreach": [gate_honesty],
}


def check(path: Path, quiet: bool = False) -> tuple[int, str | None]:
    kind = classify(path)
    if kind is None:
        return 0, None

    results = [gate_learned_rules(path, kind)]
    for gate in GATES_BY_KIND.get(kind, []):
        results.append(gate(path))

    failed = [r for r in results if r.blocking]
    lines = []
    if failed or not quiet:
        lines.append(f"gates for {path} ({kind})")
        lines += [str(r) for r in (results if not quiet else failed)]
    if failed:
        lines.append("")
        lines.append("This document is not finished. Fix these, then write it again; the gates")
        lines.append("re-run on the write. They are a floor, not a verdict: the Reviewer still")
        lines.append("has to read it. See docs/FAILURE-MODES.md.")
    return (1 if failed else 0), ("\n".join(lines) if lines else None)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run Lucy's gates against a document.")
    ap.add_argument("document", nargs="?")
    ap.add_argument("--quiet", action="store_true", help="Print only failures.")
    ap.add_argument("--list", action="store_true", help="Show what is recognised and gated.")
    args = ap.parse_args(argv)

    if args.list:
        print("Gated when a document lives under: " + ", ".join(DRAFT_DIRS))
        print("with a suffix in: " + ", ".join(sorted(DOC_SUFFIXES)))
        for kind, rx in KIND_PATTERNS:
            gates = ["learned-rules"] + [g.__name__.replace("gate_", "").replace("_", "-")
                                         for g in GATES_BY_KIND.get(kind, [])]
            print(f"  {kind:9s} matched by {rx.pattern}  ->  {', '.join(gates)}")
        return 0

    if not args.document:
        ap.error("a document path is required")
    if os.environ.get("LUCY_GATES_OFF"):
        print("gates disabled by LUCY_GATES_OFF; nothing was checked")
        return 0

    path = Path(args.document)
    if not path.exists():
        return 0                       # a deleted or moved file is not a failure
    code, out = check(path, quiet=args.quiet)
    if out:
        print(out)
    return code


if __name__ == "__main__":
    sys.exit(main())
