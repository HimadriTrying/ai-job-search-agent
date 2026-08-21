---
name: cv-tailor
description: Rewrite the master CV for one specific job description. Selects and reorders real content, tailors to the posting, runs the fresh-context Reviewer, then the honesty gate. Never invents. On demand only.
invocation: user
agent: reviewer
---

# cv-tailor — targeted CV (drafter half)

## Precedent
A drafter writes; a fresh-context reviewer critiques; the drafter revises. Output is compiled
and visually checked before it is shown.

## Inputs
`profile/05-cv-source.md`, `profile/03-writing-style.md`, `career_facts.yaml`, the target JD
**as a file** (the gate's `--job` flag needs it).

**Getting the JD from a URL — try this before asking for a paste.** Most job pages are an
ATS board rendered client-side, so fetching the HTML returns a shell with no posting in it.
Do not fetch the page. Resolve the link to its board's public JSON instead:

```
python .claude/skills/job-scout/scout/joburl.py <url> data/jd/<company>-<role>.md
```

Covers Greenhouse, Lever, Ashby and SmartRecruiters, hosted (`jobs.ashbyhq.com/acme/...`)
or embedded in a company's own careers page (`acme.com/careers?ashby_jid=...`). No key, no
login. Exits non-zero with the reason when it cannot resolve the link.

**Only if that fails**, fall back to `CLAUDE.md` → "Getting the JD": ask the user to paste
the JD text into `data/jd/<company>-<role>.md`. Never reconstruct a JD from search
snippets, and never tailor against a posting you have not actually read.

## Flow
0. **Read the rules the user has already taught you**, before drafting a line:
   `python scripts/learned_rules.py brief --scope cv`. These are their own corrections from
   earlier drafts. Re-making a correction they already made is the commonest way this skill
   looks like it has no memory.
1. Parse the JD; extract must-hit keywords and the real scope behind them.
2. Draft the CV by **selecting and reordering** from the master source — never adding.
3. **Relevance-weighted cutting** when it overflows 2 pages: score each line by
   (a) relevance to this posting, (b) uniqueness in the doc, (c) whether the cover letter
   depends on it — cut the lowest total first. An older bullet that hits posting keywords
   survives ahead of a recent bullet that doesn't.
4. Spawn the **Reviewer subagent** (fresh context) to critique; revise. If the subagent
   cannot be spawned in this environment, stop and tell the user — the drafter never
   reviews its own work as a substitute.
5. **Honesty gate**: `python honesty/verify.py <draft> --target "<Company>" --job <jd-file>`
   — must exit 0 before presenting. The flags declare the role being applied to, so naming
   the target company or echoing the JD's own terms is not treated as fabrication.
6. **Render and visually inspect**: exactly 2 pages, no orphaned titles, fonts consistent.
   LaTeX is the first choice (fix layout with `\needspace`, `\enlargethispage` and
   re-check); if the environment has no LaTeX, fall back to HTML rendered with headless
   Chromium (`chromium --headless --print-to-pdf=…`). If no PDF renderer exists at all,
   present the markdown and say a PDF could not be produced here — never let a missing
   toolchain silently skip the visual check.
7. **Learned-rule check** on the draft:
   `python scripts/learned_rules.py check <draft> --scope cv` — must exit 0.
8. Present with a verification checklist. Applying stays the human's job.
9. **If they correct the draft, run `learn`.** One question: one-off, or from now on? A
   standing rule gets written to their profile in this session, not remembered by intention.

## Hard rules
Every claim traces to `career_facts.yaml`. The gate is not optional.
**Scope travels with the claim**: a line that is true only within a scope — one market, a
pilot cohort, an average — carries that scope in the written sentence, same as it would
have to be spoken. "Live in production" when it is live in one pilot market is an
overclaim built entirely from real facts; the gate cannot catch it, so the drafter and
Reviewer must.
