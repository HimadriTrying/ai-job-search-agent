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
`profile/05-cv-source.md`, `profile/03-writing-style.md`, `career_facts.yaml`, the target JD.

## Flow
1. Parse the JD; extract must-hit keywords and the real scope behind them.
2. Draft the CV by **selecting and reordering** from the master source — never adding.
3. **Relevance-weighted cutting** when it overflows 2 pages: score each line by
   (a) relevance to this posting, (b) uniqueness in the doc, (c) whether the cover letter
   depends on it — cut the lowest total first. An older bullet that hits posting keywords
   survives ahead of a recent bullet that doesn't.
4. Spawn the **Reviewer subagent** (fresh context) to critique; revise.
5. **Honesty gate**: `python honesty/verify.py <draft>` — must exit 0 before presenting.
6. If compiling to PDF (LaTeX), **render and visually inspect**: exactly 2 pages, no orphaned
   titles, fonts consistent. Fix layout (`\needspace`, `\enlargethispage`) and re-check.
7. Present with a verification checklist. Applying stays the human's job.

## Hard rule
Every claim traces to `career_facts.yaml`. The gate is not optional.
