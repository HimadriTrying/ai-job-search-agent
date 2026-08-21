---
name: learn
description: Capture a correction the user made on a draft as a standing rule in their own profile, so it is honoured next session instead of being re-corrected. Runs when the user pushes back on generated writing and the pushback sounds like a rule rather than a one-off. Also used to list, retire, or make a stored rule mechanical.
invocation: user
---

# learn — turn a correction into a rule that survives the session

## Why this exists

A correction that only fixes the draft in front of you dies with the session. The same
correction then arrives again the following week, and the user experiences that as the agent
forgetting. It is not forgetting. The rule was never written anywhere it would be read again.

Nobody can state their writing rules up front. They discover them by rejecting drafts. So the
profile has to be able to grow after `setup`, and this skill is how it grows.

## When to run it

Whenever the user pushes back on generated writing — a CV bullet, a letter beat, an outreach
message — and the pushback is about *how they want things written* rather than about a fact
being wrong. A wrong fact is a `career_facts.yaml` problem, not a rule.

Do not wait to be asked. But do not run it on every objection either: one round-trip question
is the whole gate, and it costs a sentence.

## The one question that decides everything

> **Is this a one-off for this document, or should I keep to it from now on?**

Ask it plainly, in those terms. Then:

- **One-off** → fix the draft, store nothing, say nothing more about it. Most corrections are
  one-offs and a store full of one-offs is worse than no store.
- **Standing** → fix the draft *and* store the rule, in this session, before moving on.

**Never infer.** Silently promoting every objection to a permanent rule accumulates
contradictions that nobody can later explain, and the user ends up fighting rules they never
knowingly agreed to. Never quietly drop one either: if they said it stands, it gets written
down before the session ends.

## Before you write it down: three checks

1. **Is it theirs, or is it everyone's?** If the rule would be true for any user of Lucy, it
   belongs in the shipped house spec (`profile/06-cover-letter-notes.md` above the YOURS line,
   or the CV spec), not in one person's store. Say so, and offer to raise it upstream. The
   store is for taste, standing refusals and personal register; it is not a place to park
   universal craft rules where only one user benefits.

2. **Is a new rule even the right fix?** Read `docs/FAILURE-MODES.md`. Most repeat corrections
   are structural, not knowledge gaps: a spec re-derived instead of linked, a missing template,
   a review that arrived too late, the drafter grading its own work. For those, a new rule is
   the fix that works least often, and adding one makes the spec longer without making the
   output better. Name the class in the entry's `class:` field. **A healthy spec gets shorter
   over time.**

3. **What class does the correction belong to?** If the user objects to a specific word, ask
   what it is an instance of, and write the rule at that level. "No em dashes" returns as an
   en dash. "No dash used as punctuation" does not. Then pin the legitimate neighbours with a
   test so the widening does not overshoot: banning "passionate" must not catch "compassion".

## Writing it

```bash
python scripts/learned_rules.py add \
  --id no-spelled-out-units \
  --scope cv,letter \
  --rule "Write quantities with numerals and symbols. 30%, not thirty percent." \
  --why "Corrected on the Revolut draft, 21 Aug." \
  --class instance-scoped \
  --pattern '\b(per ?cent|percent|dollars)\b' \
  --message "spelled-out unit; use % or \$"
```

- `--scope` is `cv`, `letter`, `outreach`, `all`, or a comma-separated mix. Scope it as
  narrowly as the correction actually justifies; a rule that fires on documents it was never
  meant for is how a store becomes noise the user learns to ignore.
- `--why` is close to required in practice. **A rule whose reason nobody remembers is a rule
  nobody can safely retire**, so it stays forever and the spec only grows.
- `--pattern` is optional and worth real effort. A rule in prose is followed most of the time;
  a rule that exits non-zero is followed every time. If a mechanical form exists, add it.
- If there is no honest mechanical form, store it as prose. It still reaches the drafter
  through `brief`. Do not invent a fragile regex just to have one — a check that fires on
  legitimate text gets the whole store ignored.

Then **prove it works before telling the user it is stored**: run
`python scripts/learned_rules.py check <the draft they just corrected> --scope <scope>` and
confirm it fires on the text they objected to. A check nobody has watched fail is not known to
work. Two checks in this repo's cover-letter checker shipped silently inert for exactly that
reason.

## Telling them

One line. What was learned, where it lives, and that they can delete it.

> Stored that: quantities as numerals, for CVs and letters. It is in
> `profile/learned-rules.yaml` and it is now checked, so a draft that breaks it fails rather
> than reaching you. Delete the line if you change your mind.

Never a paragraph, and never a promise that it will "remember" — point at the file. The
learning is legible or it is not trustworthy.

## The other half: reading the rules back

Storing is useless if nothing reads them. Every drafting skill runs this **before writing**:

```bash
python scripts/learned_rules.py brief --scope letter
```

and **after writing**, as part of its checker run:

```bash
python scripts/learned_rules.py check <draft> --scope letter
```

Both halves are load-bearing. Only reading them means they are followed most of the time.
Only checking them means the model writes the wrong thing and then patches it. Doing both is
what makes a learned rule behave like a shipped one.

## Maintenance

- `python scripts/learned_rules.py list` — everything stored, with dates and whether it is
  checked or prose.
- `python scripts/learned_rules.py validate` — the store is well formed.
- **Retiring a rule is a normal thing to do.** If a stored rule keeps being overridden in
  practice, say so and offer to delete it. Ask before deleting; it is the user's file.
- If a prose rule has been corrected twice more since it was stored, that is the signal to find
  its mechanical form and add a `check:` to it.

## Hard rules

- The store is the user's file. It is gitignored, it never leaves their machine, and nothing
  goes into it that they have not agreed to in words.
- Never write a rule into a company folder or into a single document. The test is *would this
  still be true for another company?* If yes, it goes in the store.
- Never edit `career_facts.yaml` from here. Facts and rules are different things, and the
  honesty gate depends on the facts file changing only when the user's real history does.
