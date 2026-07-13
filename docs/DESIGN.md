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

## Open questions still worth resolving
- Second-degree inference from a first-degree-only export — automate vs. optimise the human ask.
- Calibrating the rubric against *outcomes* (which applications actually converted) over time.
- Whether every generative output deserves a Reviewer pass (token cost vs. quality).
- Hybrid scheduling: API for cron jobs, subscription for interactive.
- Measuring whether a warm intro actually changes conversion — the system can A/B this.
