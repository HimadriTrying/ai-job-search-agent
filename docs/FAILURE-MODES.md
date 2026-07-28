# Failure modes: why the same corrections keep coming back

This file exists because of a question the owner asked after two weeks of real use: *why do
I keep making the same corrections, when the rules are already written down?*

The answer, from the git history rather than from intuition: **of twelve repeat failures,
one was a knowledge problem and eleven were structural.** The agent was not forgetting the
rules. It was re-deriving them, not sweeping them, not asking for the brief, or grading its
own work. Writing the rules down harder would not have fixed any of the eleven.

That matters for anyone building on this repo, because the obvious response to a user
correction is to append a rule, and appending a rule is the fix that works least often. Do
it enough times and the spec becomes a memory test that the model fails in a new shape each
week.

## The classes

| Class | What it looks like | Where the fix belongs |
|---|---|---|
| **Re-derivation** | A spec describes an artefact in prose and the artefact is rebuilt from the description every time, drifting differently on each rebuild. | Make the artefact a shared asset the agent *links*. Not a rule. |
| **No correct thing to copy** | A prohibition exists ("don't copy the last one") with nothing provided to copy instead, so the forbidden path is the only path. | Ship the template. |
| **Late review surface** | The user first sees the work as a finished artefact, so every correction costs a rebuild and corrections arrive batched. | A cheap earlier checkpoint: approve the words before anything renders. |
| **Author as own critic** | The draft is reviewed by whatever wrote it, which already believes the wording is fine. | A separate pass, by something that did not write it, holding only the spec and the draft. |
| **Unswept rule** | A rule is fixed on the document that triggered it and never applied to the others. | A sweep mode, run whenever a shared file changes. |
| **Missing intake** | The agent guesses the brief instead of asking, then gets corrected on the guess. | A written brief before drafting. |
| **No machinery at all** | A whole class of deliverable has no spec, no checker, no example. | Build the machinery, seeded from real corrections rather than invented. |
| **Duplicated rule** | The same rule written in two files. One gets updated, the other goes stale and contradicts it. | One rule, one file, pointers everywhere else. |
| **Unverifiable claim** | A rule a script cannot check, treated as if stating it were enough. | Make it checkable, or route it explicitly to the critic. |
| **Rule followed, effect missed** | The spec encodes a *form* but not what the form is *for*. The draft complies with every rule and is still wrong, so the correction looks like a taste disagreement when it is a spec gap. | State the effect the shape must produce, then check a proxy for the effect. |
| **Instance-scoped rule** | The rule names the instance that got caught (`—`) instead of the behaviour (a dash used as punctuation), so the defect returns wearing a different character. | Widen to the behaviour, and pin the legitimate neighbours with a test so widening does not overshoot. |

## Three that generalise past this repo

**Gate the deliverable on its input artefact, not on a prompt instruction.** A cover letter
cannot be written until the company research file exists and is non-empty, and the letter
must then share distinctive vocabulary with it. Requiring the file catches the skipped step.
Requiring the overlap catches the case where the file exists and the model wrote from its own
memory of the company anyway. Together they are a cheap citation check for any "research then
write" pipeline, and neither needs a model call.

The failure that motivated it: a letter passed every style check on a company whose research
had never been run. The rule requiring a "researched closer" had been in the spec the whole
time. Nothing verified it, so it was decoration.

**Specify the effect, not just the shape.** A spec said "four paragraphs" and got four
paragraphs, and the user still rejected the letter, because he wanted a story and four
compliant paragraphs read as a list. Shape checks are easy to write and weak. Effect proxies
are the ones that change the output: here the effect is "the reader can retell it in one
sentence" and the proxy is a callback check, requiring the closing beat to share a
distinctive term with the opening one.

**Test the checker itself, against a known-good and a known-bad document.** Every check in
`scripts/check-cover-letter.sh` was verified by mutation: a synthetic letter that passes
everything, then one deliberate breakage per check confirming it fires, plus a confirmation
that legitimate near-misses (compound hyphens) are *not* flagged. Two checks would have been
silently inert without this. A checker nobody has watched fail is not known to work.

## The finding that limits all of the above

**Mechanical checks went green on a wrong document twice in two days.**

Once on a CV with content faults, once on a cover letter that a reviewer subagent then
returned ten violations against, including two flagship achievements where the spec allows
one, a closing line that would have been true of any competitor, and an opening that
explained the company to itself. The author had written that spec forty minutes earlier,
applied it, believed it had applied it, and passed every check.

**Mechanical checks bound the floor. They do not find the ceiling.** This is why
`cover-letter` and `cv-tailor` both run a Reviewer subagent in fresh context and why the
skills say to stop if it cannot be spawned rather than let the drafter grade itself. It is
also why `check-cover-letter.sh` prints "this is a floor, not a verdict" on success instead
of something that sounds like approval.
