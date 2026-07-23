---
name: cover-letter
description: Draft a targeted cover letter for one role, in the user's voice, grounded only in real facts. Runs the Reviewer and the honesty gate. On demand.
invocation: user
agent: reviewer
---

# cover-letter

## Precedent
Drafts a targeted cover letter from your profile and the specific JD, then runs the honesty gate.

## Inputs
`profile/06-cover-letter-notes.md`, `profile/03-writing-style.md`, `career_facts.yaml`,
the JD, and (if available) `company-research` output.

## Flow
1. Pick the angle from the notes that best fits this company's actual problem.
2. Draft in the user's voice (writing-style file). One page.
3. Reviewer subagent (fresh context) critiques for generic language and missed hooks; revise.
4. **Honesty gate** must pass:
   `python honesty/verify.py <draft> --target "<Company>" --job <jd-file>` — the flags tell
   the gate which company/JD the letter legitimately references, so only true fabrications
   fail. If PDF: render, check one page, signature visible, fonts match.
5. Present. Sending stays the human's job.
