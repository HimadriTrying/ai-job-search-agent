# CV Notes

Copy this to `profile/08-cv-notes.md` (gitignored) and fill in the sections marked **YOURS**.
Everything above those is the house spec, enforced by `scripts/check-resume.sh` and by the
Reviewer. Read it before drafting; the checker only catches the mechanical half.

Where the design lives: `templates/resume.css` and `templates/resume.html`. Layout is not
described here on purpose. A layout described in prose gets re-implemented from the
description every time and drifts differently on each rebuild, so it is an asset you link,
not a rule you follow.

---

## What a CV is actually doing

**It is skimmed before it is read.** First pass is seconds, and it is looking for a reason to
stop. Everything below follows from that: ordering by relevance beats completeness, the most
recent and most relevant work goes highest, and a page that reads as one flat block gives a
skim nothing to catch on.

**It is read alongside others.** Correct and forgettable loses to correct and specific. The
line that survives is the one only you could have written.

## The rules

**1. Bullets state outcomes, not duties.** "Responsible for the payments roadmap" tells the
reader your job description. "Cut failed payments from 4% to 1.2% by rebuilding the retry
logic" tells them what happened when you did it. If a bullet would still be true of anyone
who held the title, it is a duty, and it is costing you a line.

**2. One flagship per role. Everything else is support.** Three achievements at equal weight
leaves the reader to work out which one matters, and they will not: they will skim past all
three. Mark the flagship (`class="flagship"` in the template), keep it first, and let the rest
be shorter.

**3. A change keeps both sides.** "From 60 days to 30" is a result. "To 30 days" is a number
with no story, and the reader cannot tell whether it is an improvement. The baseline is the
half that makes the claim mean anything, and it is the half that gets dropped when a line is
trimmed for space.

**4. Quantities use numerals and symbols.** 30%, not thirty percent. $2M, not two million
dollars. Spelled-out numbers read as prose and disappear in a skim; a skim is looking for
digits.

**5. A named list does not collapse into a count.** "Integrated Shopify, Stripe and Adyen"
survives; "integrated three major platforms" does not. Names are searchable, checkable, and
carry the weight the count throws away. Collapse only when the names genuinely add nothing.

**6. Scope travels with the claim.** A line true only within a scope carries that scope in the
sentence. "Live in production" when it is live in one pilot market is an overclaim built
entirely from real facts, so the honesty gate cannot catch it. You and the Reviewer are the
only layers that can.

**7. Cut by relevance, not by age.** When it overflows, score each line on how much it answers
THIS posting, how much it repeats something already on the page, and whether the cover letter
depends on it. Cut the lowest total. An older bullet that hits the posting's language survives
ahead of a recent one that does not.

**8. Two pages, unless you have declared one.** Longer is not more complete, it is less read.

**9. Never template off a previous CV.** A prior output carries that application's tailoring
decisions along with its layout, so the new document inherits a shape chosen for a different
posting. Start from `templates/resume.html`, every time. (A prohibition with nothing to copy
instead is a trap, which is why the template exists.)

**10. Approve the words before anything renders.** Show the content sheet as plain text first:
headline, summary, and the bullets grouped by role, plus what was cut and why. Content,
wording and layout arriving together means every correction costs a full rebuild.

## What the checker enforces

`bash scripts/check-resume.sh <resume.html>` (add `--all` to sweep every CV after a shared
file changes):

* the design system is linked, not inlined
* no page clips its own overflow, so the page count can tell the truth
* type hierarchy holds: section heading larger than role heading, larger than body
* quantities are numerals, not spelled out
* before/after claims keep both sides
* no placeholders, and a contact block exists
* page count and embedded fonts, when a renderer is available
* your own learned rules, from `profile/learned-rules.yaml`

**Passing is a floor, not a verdict.** In real use a CV passed every mechanical check and was
still returned with content faults. Rules 1, 2, 6 and 7 are the expensive ones and no script
can see any of them. See `docs/FAILURE-MODES.md`.

---

## YOURS: what always leads
<!-- The proof you want read first, unless the posting says otherwise. -->

## YOURS: sections you always keep, and always cut
<!-- e.g. "side projects always stay, they carry the AI work"; "no interests section". -->

## YOURS: theme
<!-- Fonts and colours live in the :root block of templates/resume.css. Note here WHY you
     chose them, so a later session does not undo it. -->

## YOURS: hard nos
<!-- Things you refuse to claim or say on a CV, even where they would help. -->
