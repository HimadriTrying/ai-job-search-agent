---
name: cover-letter
description: Draft a targeted cover letter for one role, in the user's voice, grounded only in real facts. Requires company research, runs the style checker, the Reviewer and the honesty gate. On demand.
invocation: user
agent: reviewer
---

# cover-letter

## Precedent
Drafts a targeted cover letter from your profile and the specific JD, then runs the style
checker, the Reviewer and the honesty gate.

## Inputs
`profile/06-cover-letter-notes.md` (**the house spec: read it in full before drafting**),
`profile/03-writing-style.md`, `career_facts.yaml`, the JD **as a file** (see `CLAUDE.md` →
"Getting the JD": unfetchable URL → ask the user to paste the text into
`data/jd/<company>-<role>.md`; never reconstruct a JD from search snippets), and the
`company-research` output, which is **required, not optional** (see step 0).

## Flow

0. **Research first, or stop.** The letter's opening beat is a researched observation, so
   `data/research/<company>.md` (or `<company>/company-research.md`) must exist and be
   non-empty. If it does not, run `company-research` first, or tell the user the letter is
   not ready to draft. Do not substitute the model's own memory of the company: a letter
   that cites a company fact nobody researched will pass every style check and still be
   wrong, which is exactly the failure this step exists to prevent.
1. **Pick the spine, not the angle.** One thing the research surfaced that your own
   experience answers. It must relate to the role or the domain, and it must be something
   only real research would find. Check it against the four tests in the notes file.
2. **Draft as one story in four beats**, per the notes file: observation, flagship proof,
   turn, callback. In the user's voice (writing-style file). 200 to 280 words.
3. **Run the style checker** and fix everything it reports:
   `bash scripts/check-cover-letter.sh <draft.md> --company "<Company>"`
4. **Reviewer subagent** (fresh context) critiques against `profile/06-cover-letter-notes.md`,
   which it should be given along with the draft and nothing else. It is looking for what the
   checker cannot see: two flagships where the spec allows one, a closer that would be true
   of a competitor, an opening that explains the company to itself, a win dressed as a
   constraint. Revise. **If the subagent cannot be spawned, stop and tell the user.** The
   drafter never reviews its own work as a substitute; in real use, a draft that passed all
   eight mechanical checks came back from the Reviewer with ten violations of the spec its
   own author had written.
5. **Honesty gate** must pass:
   `python honesty/verify.py <draft> --target "<Company>" --job <jd-file>` — the flags tell
   the gate which company/JD the letter legitimately references, so only true fabrications
   fail. If PDF: render, check one page, signature visible, fonts match.
6. Present. Sending stays the human's job.

## What passing means

The checker is a floor, not a verdict. It proves the letter is the right length, names the
right company, invents no numbers, and is structurally a story rather than a list. It cannot
tell you the argument is any good. Steps 4 and 5 are what make it safe to send; step 3 only
makes it worth their time to read. See `docs/FAILURE-MODES.md`.
