# Publishing this repo to GitHub

This package is clean and safe to publish: it contains the system and `*.example`
templates only. Your personal files are not here and are gitignored, so filling them
in later will not leak them.

## One-time: put it on your GitHub

1. Create a new **empty** repo on github.com (no README/license — this repo has them).
   Suggested name: `ai-job-search-agent`.
2. In this folder, run:

   ```bash
   git init
   git add .
   git commit -m "Job Search Orchestrator: conversational multi-agent job search on Claude Code"
   git branch -M main
   git remote add origin https://github.com/<you>/ai-job-search-agent.git
   git push -u origin main
   ```

3. Edit `LICENSE` to replace `<YOUR NAME>`.

## Automated guard (set up once)

A pre-commit hook refuses to commit private data — it blocks the known private paths
(even if force-added with `git add -f`) and scans staged content for your real names,
email, and employer names. Enable it once per clone:

```bash
git config core.hooksPath .githooks
```

The hook (`.githooks/pre-commit` → `scripts/check-private.sh`) reads your private tokens
from `.private-guard`, which is **gitignored** — the token list never enters the public repo.
If you clone this fresh, recreate `.private-guard` (one token per line) and re-run the command
above. In a genuine false positive: `git commit --no-verify` (sparingly).

## Pre-push checklist (30 seconds, do it every time)

```bash
# 1. Nothing personal should appear here:
git status --short
# 2. The ignore rules must be active — each must print a path:
git check-ignore career_facts.yaml profile/01-candidate-profile.md data/tracker.csv
# 3. No tracked file contains a private token (reads your gitignored .private-guard —
#    so this command names no one):
git grep -iFf <(grep -vE '^[[:space:]]*(#|$)' .private-guard) -- . && echo "^ REVIEW" || echo "clean ✓"
```

If step 2 prints nothing, or step 3 prints a filename, **STOP — do not push.**

## When you fill in your profile later

Your real `career_facts.yaml` and `profile/0X-*.md` (without `.example`) are gitignored.
Work in them freely; they stay on your machine. The public repo keeps only the `.example`
versions so others can fork and fill their own.

## Toward a product
The DESIGN.md and the skill structure are built to generalize. When you're ready to turn
this from a personal repo into a product, the natural next steps are: a hosted setup flow
(so users don't hand-edit YAML), a profile importer (LinkedIn/CV → career_facts), and a
managed scheduler. None of that is needed to publish today.
