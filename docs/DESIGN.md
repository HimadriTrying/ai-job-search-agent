# Design rationale

## The thesis
Job search is a funnel, and the interesting failures are between the stages, not inside them.
Discovery is solved. Doc quality is solved. Submission is nearly solved. What's unsolved is
(a) a single surface to drive the whole funnel and (b) the warm-intro layer. So that's where
this system spends its originality.

## Why an orchestrator, not more slash commands
Slash commands make you the router — you have to know which command fits. An orchestrator
(`CLAUDE.md`) lets you describe intent and routes for you, and it can *chain* stages ("go after
this role" → research → tailor → network → track). Specialists are still individually invocable
as skills, so you lose nothing.

## Why the honesty gate is code, not a prompt
"Never fabricate" as a prompt is a promise. `verify.py` against a frozen `career_facts.yaml` is
a guarantee that fails loudly on drift. The gate catches invented entities, credentials, and
metrics; the fresh-context Reviewer catches spin. Neither alone is enough; together they cover
most of the risk surface.

The same reasoning produced `scripts/check-cover-letter.sh`: the gate proves a document does not
lie, and the style checker proves it is not generic. Both are floors. Real use has twice
produced documents that passed every mechanical check and were still returned by the Reviewer
with content faults, which is why the drafting skills stop rather than let the drafter grade
itself. The full account is in [FAILURE-MODES.md](FAILURE-MODES.md), including why answering a
user correction with another rule is usually the wrong fix.

## Why the gates are code that runs itself, not steps in a skill

Every check in this repo already exits non-zero. The weakness was never the checks. It was that
running them was a **step a model performs**, and a skipped step leaves no trace, so a document
nobody checked looks exactly like one that passed. A cover letter went out green on a company
whose research had never been run; the rule requiring research had been in the spec the whole
time.

Sort the guarantees by who is responsible for making them happen:

| Who runs it | Example | Strength |
|---|---|---|
| The harness, unconditionally | git pre-commit privacy guard, PostToolUse hooks | Cannot be skipped |
| Code, if something invokes it | `honesty/verify.py`, `check-cover-letter.sh` | Real teeth, no trigger |
| Prose in a spec | "spawn the Reviewer", "research first" | Followed most of the time |

Before this change the repo had exactly one unconditional content guarantee, and it was spent
on em dashes in the marketing page, while the honesty gate sat in the middle row. So the
mechanism was already proven; it was pointed at the least important rule in the system.

Now: writing a draft runs its gates, and the turn cannot end while a draft has never passed or a
user correction is unresolved. Three things this deliberately does **not** do. It does not
replace the steps in the skills, which still run the checks explicitly so failures arrive during
drafting rather than after: the gates are the backstop, not the plan. It does not block when a
gate *cannot* run, because locking a half-set-up user out of their own drafts is a worse failure
than the one it prevents. And it stops blocking after three refusals, because a gate that can
never be satisfied burns quota in a loop the user did not ask for and cannot see.

**The gates live in `gates/`, not in the hooks.** Hooks are Claude Code's affordance; the day
Lucy runs on an API loop or a hosted surface, `.claude/settings.json` is not there and every
guarantee written into it silently evaporates. `.claude/hooks/gate-on-write.sh` and
`close-the-loop.sh` are nine-line adapters that parse the hook payload and call `gates/run.py`.
Adapters are disposable. Gates are not.

## Why the CV spec is an asset and the Reviewer is a gate

Two halves of the same finding, from the failure taxonomy.

**The design system is a file, not a description.** `templates/resume.css` holds the sizes,
colours and spacing once, and a CV links it. The alternative, a spec describing the layout in
prose, gets re-implemented from the description on every rebuild, so no single CV is wrong and
no two agree. Making it an asset removes the whole class at a stroke: a document that links the
stylesheet cannot hold its own copy to get wrong. `check-resume.sh` therefore fails a CV that
inlines the design system, which is the one rule that keeps the asset load-bearing rather than
decorative. And because a prohibition with nothing to copy instead is a trap, `templates/
resume.html` ships alongside it: "never template off a previous CV" only works if there is
something else to start from.

Two details in that stylesheet are not taste. A page uses `min-height` and `overflow: visible`,
because `overflow: hidden` on a fixed-height page silently deletes the content that does not
fit while still reporting the page count you wanted, so the document lies about being finished.
And an explicit `@page { margin: 0 }` stops the browser adding its own print margin on top of
the page box, which made a one-page CV render as two and put every page-count check off by one.
That one was found by rendering, not by reading.

**The Reviewer is the last thing that was still only asked for.** Every mechanical check in
this repo exits non-zero, and after the gates they all run whether or not anything remembers
them. The Reviewer did not: every reference to it in code was a comment telling somebody to run
it. That matters because the mechanical checks bound the floor and the faults that actually
cost rounds are above it, where no script can see: a bullet stating a duty rather than an
outcome, three achievements at equal weight, a claim true only inside a scope it never names.

So a draft that has passed every check but has never been read is now an open item, and the
turn does not end. The receipt is the critique itself; a one-word note is refused, and editing
the draft invalidates it, since the Reviewer is only useful on the text that will actually be
sent. **This is a forcing function, not a signature.** It cannot prove the Reviewer ran. What
it guarantees is that nobody can call a draft finished while nothing at all has been filed,
which is a smaller claim and the honest one.

## Why filters drop instead of downrank
Scoring an out-of-band role still spends a model call. Dropping it before scoring is cheaper
and cleaner. The one inversion this candidate needs: the seniority knob drops roles *below*
Senior, not above — the opposite of a junior-candidate filter.

## Why the human stays at the point of commitment
Every reference system stops before auto-submitting. So does this one — two independent locks on
`submit`, no batch path. The cost of an automated mistake here (a wrong application, a tone-deaf
outreach) is borne by a real relationship, so the human clicks the button.

## Cost model
Automate the cheap and repetitive (discovery, nudges); keep the expensive and judgment-laden on
demand (tailoring, outreach, negotiation). On a subscription the binding constraint is rate
limits, not dollars — a heavy overnight job can starve the interactive quota, so scheduling is
deliberately narrow.

## Why the product learns your style instead of shipping one

Every style rule in this repo was paid for, one correction at a time, by one person using the
tool on his own job search. That is the right way to *find* the rules and the wrong way to know
which of them belong in a product. Dogfooding produces two kinds of rule and they are
indistinguishable in the moment: rules that are true of any good document, and rules that are
this owner's taste. Only one question separates them, and it has to be asked every time — *would
this still be true for someone else?*

So the specs ship in two halves, and `profile/06-cover-letter-notes.example.md` is the reference
implementation of the split. Above the line is the house spec: the four-beat shape, what counts
as a researched point, the rules the checker enforces. Universal, committed, and the same for
everyone. Below the line are sections marked **YOURS** — recurring angles, signature stories,
hard nos — shipped empty and gitignored once filled. **A new user's own file is the only place
their taste is allowed to live.** Anything the owner's taste touches (typefaces, colours, which
roles lead) belongs below that line or in a theme file, never in the shipped spec.

### The half that was missing: nothing ever fills YOURS in

`setup` asks for voice once, in a single question, at the beginning — which is the moment the
user knows least about their own rules. Nobody can state their writing rules up front. They
discover them by rejecting drafts. The owner's own cover-letter spec took six rounds of
correction to arrive at, and it exists today only because each correction was written into the
governing file in the same session it was made.

The product had no equivalent of that step. A user corrects a draft, the draft gets fixed, the
correction dies with the session, and the same correction arrives again the following week. That
reads to the user as the agent forgetting. It is not forgetting: the rule was never written
anywhere it would be read again.

So a correction is treated as a product input, not as chat:

- **Ask, do not infer.** On a pushback, Lucy asks whether this is a one-off for this document or
  a standing rule. Silently promoting every objection to permanent law accumulates contradictions
  and one-off preferences that nobody can later explain, which is the same failure as a spec that
  only ever grows.
- **Write it where it will be read.** A standing rule goes into the user's own profile file in
  the same session, in the YOURS half. The repo already states this principle for its own copy
  rules ("a rule that lives only in a conversation dies with that session"); this generalises it
  to the user's documents.
- **Prefer a check to a sentence.** Where the rule is mechanically checkable, it is added to the
  checker as well, because a rule stated in prose is followed most of the time and a rule that
  exits non-zero is followed every time.
- **Record the class, not only the fix.** [FAILURE-MODES.md](FAILURE-MODES.md) exists because
  answering every correction with another rule converges on a spec that is a memory test. The
  loop asks which class of failure a correction represents, so the fix can go at the cause. A
  healthy spec gets shorter over time, not longer.

### How it is actually wired

- **The event.** There is no "the user rejected the draft" event to subscribe to. The closest
  real one is the user submitting a prompt, so `.claude/hooks/correction-nudge.sh` listens on
  `UserPromptSubmit`, matches a tight list of correction-shaped phrases, and injects a reminder
  at the moment of the correction. `CLAUDE.md` carries the same rule, but a rule near the top of
  a long session competes with everything since; a line injected at the moment does not. It is a
  nudge, not a guarantee, and it is rate-limited to once every 15 minutes so it cannot become
  nagging. A prompt that always fires is one that gets ignored, the same way a checker that is
  always red gets ignored.
- **The store.** `profile/learned-rules.yaml`, gitignored, with a shipped `.example` carrying
  the schema. Each entry has an id, a date, a scope (cv / letter / outreach / all), the rule in
  one sentence, why it exists, optionally which failure class it was, and optionally a
  mechanical `check:`.
- **Both halves, or neither.** `learned_rules.py brief` is read by the drafting skills *before*
  writing; `learned_rules.py check` runs *after*, wired into `scripts/check-cover-letter.sh` as
  its last step. Only reading them means they are followed most of the time. Only checking them
  means the model writes the wrong thing and then patches it.
- **Prose is a first-class citizen.** Most real corrections have no honest mechanical form. They
  are still stored and still reach the drafter. Inventing a fragile regex to make a rule look
  enforced is worse than storing it as prose, because one false positive teaches the user to
  ignore the whole store.
- **Its context cost is bounded on purpose.** The loop runs on every session and before every
  draft, so an unmeasured version of it would quietly eat the user's rate-limit quota, which is
  the binding constraint on a subscription. What it costs: about 160 tokens of `CLAUDE.md` per
  session, a 43-token skill description, a nudge of roughly 120 tokens at most once per fifteen
  minutes, and a brief that is scoped to the document type and prints the rule without its
  reason (the drafter needs the instruction; the reason is for the human deciding whether to
  retire it). That last choice roughly halves the recurring cost. The `learn` skill's 1,700-token
  body loads only when a correction is actually being stored. Past 25 rules in one scope the
  brief says so and asks for consolidation, because a store that only grows is both a memory
  test and a per-draft tax.
- **Tested by mutation.** Every check is proved twice, once firing and once staying quiet,
  including that widening a rule does not overshoot its legitimate neighbours. Two checks in the
  cover-letter checker shipped silently inert before this was a habit.

### What this does not mean

It does not mean the agent tunes itself quietly in the background. Every rule it learns is a
line in a file the user can read, edit, and delete, in their own copy, on their own machine.
The learning is legible or it is not trustworthy.

## Landing page: owner decisions (so no session relearns them)

Reference the owner likes: withtitan.com. Numbered pictorial panels, ruthless brevity, and the
page closes on the same CTA it opened with.

- **Copy rules are enforced in code.** No em or en dashes in `docs/*.html`; quantities as
  numerals ("11 years"). See `scripts/check-copy-style.sh`, wired as a PostToolUse hook.
- **The 6 stages keep the numbered rail with 1 panel at a time** (auto-advancing, click a
  node to pin). A full left-to-right card grid was tried on 2026-07-23 and the owner
  preferred the rail; do not reintroduce the grid for the stages.
- **The click-to-light-up interaction lives on the 3 rule cards** ("3 rules it can't
  break"): clicking a card flips it to the brand gradient. Keyboard accessible
  (Enter/Space, aria-pressed).
- **Every stage gets a small SVG diagram** in the brand palette, decorative and aria-hidden,
  hidden on small screens. No invented numbers inside diagrams: the honesty rule covers
  pictures too.
- **Typewriter headline plays once** on load, then rests on the final promise. Deliberate:
  a headline that keeps rewriting itself steals attention. It also sits out entirely under
  reduced motion. Do not make it loop without the owner asking.
- **The page ends on a closing CTA** mirroring the hero (try in browser / set up the agent).
- **About section is in the owner's own words** (11 years, both sides of the table). Do not
  replace it with drafted marketing copy. Portrait lives at `docs/assets/profile.jpg`
  (public by the owner's choice); employer logos in `docs/assets/logos/`.
- **Previews:** artifact previews are private snapshots for unmerged work; the public
  preview is GitHub Pages once enabled (Settings → Pages → `main` `/docs`).

## Open questions still worth resolving
- Second-degree inference from a first-degree-only export — automate vs. optimise the human ask.
- Calibrating the rubric against *outcomes* (which applications actually converted) over time.
- Whether every generative output deserves a Reviewer pass (token cost vs. quality).
- Hybrid scheduling: API for cron jobs, subscription for interactive.
- Measuring whether a warm intro actually changes conversion — the system can A/B this.
