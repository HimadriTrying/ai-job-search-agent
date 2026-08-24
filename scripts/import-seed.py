#!/usr/bin/env python3
"""
import-seed.py — turn the try page's profile seed into a real profile.

WHY THIS EXISTS

The try page (docs/try.html) already asks for the single most valuable thing a new user has:
their whole CV. It tailors it, renders it, and then the tab closes and all of it is gone. The
next step, installing the agent, opens with `run setup` and an interview measured in sessions.

So the funnel asks for hours of work before showing any output, when the material for a decent
first profile was already pasted in and thrown away. This closes that: the page hands back a
seed file, and this writes it into the two files that matter most.

    python scripts/import-seed.py ~/Downloads/lucy-profile-seed.json

THE IMPORTANT PART: THESE FACTS ARE NOT VERIFIED

`career_facts.yaml` is the frozen truth the honesty gate checks every document against. A seed
is a MODEL'S READING of a CV, so it can mis-parse a date, attach a metric to the wrong
employer, or quietly drop a qualifier. Importing one and trusting it would turn the strongest
guarantee in this system into a guess wearing its uniform.

So the imported file is stamped `verified: false`, and the gate says so on every run until a
human has read it line by line and flipped it. That is the whole point of the flag: it makes an
unread facts file loud rather than invisible.

Exit codes: 0 wrote, 1 refused (target exists, or the seed is malformed), 2 usage.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("Missing dependency: pip install pyyaml\n")
    sys.exit(2)

REPO = Path(__file__).resolve().parents[1]

FACTS_HEADER = """# ─────────────────────────────────────────────────────────────────────────────
# career_facts.yaml — THE FROZEN SOURCE OF TRUTH
#
# ⚠  IMPORTED FROM A TRY-PAGE SEED ON {today}. NOT YET VERIFIED BY A HUMAN.
#
# Everything below was read out of your CV by a model. That is a good starting point and a
# bad source of truth: a date can be mis-parsed, a metric can end up under the wrong
# employer, a qualifier can go missing. The honesty gate checks every document you generate
# against THIS FILE, so an error here becomes an error the gate cannot see.
#
# Read it line by line. Delete anything you would not say under oath in a reference check.
# Then set `verified: true` below, and the gate will stop warning you.
# ─────────────────────────────────────────────────────────────────────────────

"""

CV_SOURCE_HEADER = """<!--
  05-cv-source.md — your master CV content, imported from a try-page seed on {today}.

  This is the uncut raw material `cv-tailor` selects and reorders from. It is not itself a CV
  and it is not length-limited: the more real detail here, the better every tailored version
  gets. Add the projects, the numbers and the context your CV had no room for.

  Imported automatically, so it is only as good as the CV that was pasted in. Run `/setup` to
  deepen it, which is where the real quality comes from.
-->

"""


def fail(msg: str) -> int:
    sys.stderr.write(f"{msg}\n")
    return 1


def load_seed(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"Could not read {path} as JSON: {exc}\n")
        return None
    if not isinstance(data, dict) or "career_facts" not in data:
        sys.stderr.write(
            f"{path} does not look like a Lucy profile seed (no 'career_facts' key).\n")
        return None
    return data


def summarise(facts: dict) -> list[str]:
    """What a human should check first, in the order they should check it."""
    out = []
    cand = facts.get("candidate") or {}
    out.append(f"name: {cand.get('name') or '(missing)'}")
    out.append(f"location: {cand.get('location') or '(missing)'}")
    employers = facts.get("employers") or []
    out.append(f"employers: {len(employers)}")
    for e in employers:
        metrics = e.get("metrics") or []
        span = f"{e.get('start') or '?'} to {e.get('end') or '?'}"
        out.append(f"   {e.get('company') or '(no company)'} — {e.get('title') or '(no title)'}"
                   f" — {span} — {len(metrics)} metric(s)")
    out.append(f"education: {len(facts.get('education') or [])}")
    out.append(f"certifications: {len(facts.get('certifications') or [])}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Import a try-page profile seed.")
    ap.add_argument("seed", help="Path to lucy-profile-seed.json")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite career_facts.yaml / profile/05-cv-source.md if they exist.")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be written, write nothing.")
    args = ap.parse_args(argv)

    seed_path = Path(args.seed).expanduser()
    if not seed_path.exists():
        return fail(f"No such file: {seed_path}")
    seed = load_seed(seed_path)
    if seed is None:
        return 1

    facts = seed.get("career_facts")
    if not isinstance(facts, dict):
        return fail("'career_facts' in the seed is not a mapping.")

    # Never import a seed that already claims to be verified. Verification is a human reading
    # the file; a flag arriving pre-set would be a claim nobody made.
    facts["verified"] = False
    facts["imported_from_seed"] = date.today().isoformat()

    facts_path = REPO / "career_facts.yaml"
    cv_path = REPO / "profile" / "05-cv-source.md"
    today = date.today().isoformat()

    targets = [(facts_path, "career_facts.yaml"), (cv_path, "profile/05-cv-source.md")]
    # A symlink counts as existing, and counts harder. scripts/sync-private.sh links these
    # paths at a separate private repo, and write_text() follows a symlink: importing over one
    # would silently overwrite the real, verified history it points at with a fresh model's
    # reading of a CV. That is the worst outcome this script could possibly have.
    existing = [name for p, name in targets if p.exists() or p.is_symlink()]
    if existing and not (args.force or args.dry_run):
        return fail(
            f"Refusing to overwrite: {', '.join(existing)} already exist.\n"
            "Your real history is worth more than an import. Move them aside, or pass --force "
            "if you are certain.")

    print(f"From {seed_path.name}:")
    for line in summarise(facts):
        print(f"  {line}")
    print()

    if args.dry_run:
        print("Dry run: nothing written.")
        return 0

    # Even under --force, replace a symlink rather than writing through it: the file the user
    # meant to overwrite is the one in THIS repo, never whatever it points at elsewhere.
    for path, _ in targets:
        if path.is_symlink():
            print(f"Replacing symlink {path.name} (its target is left untouched)")
            path.unlink()

    body = yaml.safe_dump(facts, sort_keys=False, allow_unicode=True, width=95)
    facts_path.write_text(FACTS_HEADER.format(today=today) + body, encoding="utf-8")
    print(f"Wrote {facts_path.relative_to(REPO)}")

    cv_source = seed.get("cv_source") or ""
    if cv_source.strip():
        cv_path.parent.mkdir(parents=True, exist_ok=True)
        cv_path.write_text(CV_SOURCE_HEADER.format(today=today) + cv_source.strip() + "\n",
                           encoding="utf-8")
        print(f"Wrote {cv_path.relative_to(REPO)}")
    else:
        print("No cv_source in the seed; profile/05-cv-source.md left alone.")

    print()
    print("NEXT, AND DO NOT SKIP IT:")
    print("  1. Read career_facts.yaml line by line. A model read it out of your CV, so a date")
    print("     can be wrong or a metric can sit under the wrong employer. Delete anything you")
    print("     would not say under oath in a reference check.")
    print("  2. Set `verified: true` at the end of the file. Until you do, the honesty gate")
    print("     warns on every run, because it is checking documents against unread facts.")
    print("  3. Run `/setup` to fill in the rest: how you work, your voice, your STAR stories.")
    print("     The seed covers the facts. Everything that makes output sound like you is still")
    print("     ahead of you, and it is where the quality actually comes from.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
