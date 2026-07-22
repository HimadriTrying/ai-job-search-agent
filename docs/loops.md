# Loop engineering in Lucy

Lucy's automation follows the loop-engineering pattern: you don't prompt the agent —
you design the **loop that prompts the agent**, and you keep the human at the
accountability boundary. (See Addy Osmani's "Loop Engineering" and Linas Beliūnas's
complete guide; this file maps the pattern onto Lucy.)

## The two loops

- **Inner loop (Lucy's):** investigate → produce → verify → repeat. Skills do the work;
  the Reviewer subagent and the honesty gate (`honesty/verify.py`) verify it. The
  generator never grades its own homework: the Reviewer runs with fresh context, and the
  honesty gate is deterministic code, not model judgment.
- **Outer loop (yours):** review what the loops produced and make the calls that matter.
  In Lucy this boundary is an axiom: **the human commits — applies, sends, accepts —
  never the agent.** The `submit` skill's two locks are that gate made explicit.

## The five components, in Lucy terms

| Loop-engineering component | Lucy's implementation |
|---|---|
| External state / memory | The private companion repo: `data/tracker.csv` (the backlog), `data/digests/`, `processes/`. Every loop reads state from there and writes state back there — a loop without write-back is amnesia. |
| Automations (triggers) | Scheduled runs (below) — cron wakes a fresh headless session, it does one bounded job, reports, stops. |
| Skills | `.claude/skills/*` — each a bounded, single-purpose worker. |
| Sub-agents, split roles | Execution (e.g. `cv-tailor`) vs verification (Reviewer, honesty gate) are separate agents with separate instructions. |
| Quality gates | Deterministic first (`honesty/verify.py`, `scripts/check-private.sh` pre-commit guard), model-judgment second (Reviewer), human always last. |

## Loop contracts

Every scheduled loop declares: trigger · inputs · definition of done · gates · budget ·
escalation · report-back. A loop missing any of these isn't enabled, it's loose.

### 1. Morning scout (daily, weekdays)

- **Status: designed, NOT armed.** Arm it (as a Routine or via the Actions secrets)
  only once its inputs exist — scout config, watchlist, and tracker in the private
  repo. Until then there is nothing to pick up, and a loop with no inputs just burns
  quota reporting emptiness.
- **Trigger:** cron, 06:00 UTC weekdays.
- **Inputs:** `job-scout` config + watchlist, tracker (all from the private repo).
- **Definition of done:** dated digest written to `data/digests/` (resolves into the
  private repo) with apply-first / worth-a-look / skipped, PLUS follow-up nudges from
  tracker elapsed-time rules. If inputs are missing, the digest says so — a loop that
  can't run reports that it can't run; it never pretends.
- **Gates:** nothing written to the public repo (guard-enforced); no tailoring, no
  outreach — discovery only.
- **Budget:** one bounded pass; this is the cheap loop. On a subscription the scarce
  resource is rate limit, not dollars — the loop must never eat the interactive quota.
- **Escalation / report-back:** short summary via session notification; state changes
  committed and pushed inside `private/`.

### 2. Weekly network-map refresh

Same contract shape; runs weekly; requires `data/connections/` export in the private
repo. **Not armed until that data exists** — arming a loop whose inputs don't exist
just burns quota to report emptiness.

### 3. What stays OUT of loops (deliberately)

CV tailoring, cover letters, outreach, negotiation, anything that commits you.
Judgment-laden work is on-demand; the outer loop — you — initiates it. This is the
same cost-control principle CLAUDE.md states, now with a name: those are outer-loop
actions, and automating the outer loop is the loop-engineering anti-pattern.

## Two runtimes for the same loops

1. **Claude scheduled Routines** (recommended on a Claude subscription): the trigger
   fires a fresh headless session in the managed environment, which has GitHub-App
   access to both repos. No API key to manage; respects the subscription.
2. **GitHub Actions** (`.github/workflows/daily-scout.yml`): the API-key path, kept as
   a public reference implementation. Requires two secrets — `ANTHROPIC_API_KEY` and
   `LUCY_PRIVATE_TOKEN` (a fine-grained PAT with read/write on the private data repo) —
   because the loop's inputs and outputs both live in the private repo. Without them it
   exits early by design.

## Design rules learned the hard way

- **State first.** The original daily-scout workflow ran in a public checkout where its
  inputs were gitignored (absent) and its output path was gitignored (uncommittable).
  It looped, but it couldn't remember or deliver. Wire the state before the schedule.
- **Graceful absence.** Every loop checks its inputs exist before doing work, and its
  report distinguishes "nothing found" from "couldn't look".
- **Verify away from the generator.** Reviewer ≠ writer; gate ≠ either.
- **The loop stops.** One pass, bounded scope, explicit end. Anything unbounded needs
  a human at the wheel.
