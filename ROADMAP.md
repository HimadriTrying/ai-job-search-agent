# Roadmap

Where Lucy is, and where it's going. This roadmap tracks the whole job-search funnel —
discovery → fit → tailored docs → warm intro → apply → track → interview → offer → negotiate —
and is deliberately honest about what actually works versus what is merely scaffolded.

Each item carries a one-line hypothesis: the bet we're making by building it.

**Status key:** ✅ shipped · 🔨 in progress · ⬜ planned · ⏸️ parked

---

## Shipped

- ✅ **Orchestrator (Lucy)** — the single conversational surface. `CLAUDE.md` routes plain-language
  requests to the right specialist and synthesises the result; there are no commands to memorise.
  *Hypothesis: one agent you talk to beats a toolbox of commands, because the barrier to job-hunting is effort, not features.*

- ✅ **Honesty gate** — `honesty/verify.py` checks every outbound document against the frozen
  `career_facts.yaml` before it can leave the system. Invent an employer, credential, or metric and it fails loudly.
  *Hypothesis: enforcing "never fabricate" in code, not just a prompt, is what makes an AI safe to represent a real person's history.*

- ✅ **Discovery + scoring** — the `job-scout` skill sweeps public ATS APIs, drops out-of-band roles
  before spending a model call, and scores survivors with a penalty-first rubric that filters hard instead of flattering.
  *Hypothesis: most good roles are missed, not rejected; a daily automated sweep surfaces what manual searching misses.*

- ✅ **Seniority floor filter** — a floor in `profile/04-job-evaluation.md` that drops anything below
  Senior — the inverse of the usual junior-candidate filter.
  *Hypothesis: senior candidates waste time filtering out junior roles; inverting the usual filter removes that noise.*

- ✅ **Model routing** — the cheap work (out-of-band pre-filtering) runs before any model call at all;
  paid judgment is routed to where it's actually needed.
  *Hypothesis: the cheapest component is the one that isn't a model call; routing spend to where judgment is actually needed cuts cost without cutting quality.*

- ✅ **Privacy by design** — personal data stays gitignored; a `pre-commit` guard (`scripts/check-private.sh`)
  blocks private files and identifying tokens from ever reaching this public repo.
  *Hypothesis: people will only trust a job tool with their real history if that data never leaves their own machine.*

- ✅ **Voice / style framework** — a codified writing-style spec (`profile/03-writing-style.md`,
  `profile/06-cover-letter-notes.md`) that strips the usual AI tells so generated documents sound
  like the actual person. Tuned to the primary user today; generalising it to any user is future work.
  *Hypothesis: documents that sound like a language model get discarded; a codified voice framework — even one tuned to a single person — is what makes generated writing usable without a rewrite.*

- ✅ **Interview-prep guidelines** — the `interview-coach` prepares you from the interviewer's seat,
  feeding on hiring-side rubrics (how interviewers score, structure loops, and write the JD) inverted
  into prep. Grounded in a personal STAR bank that is still being filled in.
  *Hypothesis: preparing from the interviewer's seat — the scoring rubric inverted — beats rehearsing answers blind, because you prepare for what interviewers actually evaluate.*

- ✅ **Token-efficiency layer** — sessions run behind [rtk](https://github.com/rtk-ai/rtk), a
  hook that compresses shell-command output before it reaches the context window. Installed
  automatically at session start on the web and in the daily-scout workflow; degrades to a no-op
  if unavailable. Paired with a minimal-code rule in `CLAUDE.md` (distilled from
  [ponytail](https://github.com/DietrichGebert/ponytail)'s laziness-ladder idea, kept to a few
  lines rather than a per-session ruleset) for work on Lucy's own code.
  *Hypothesis: on a subscription the scarce resource is rate-limit quota, not dollars; shrinking what the model reads protects the interactive quota without touching what it writes.*

- ✅ **Cover-letter style checker** — `scripts/check-cover-letter.sh`, the letter-side counterpart
  to the honesty gate. The gate proves a document doesn't lie; this proves it isn't generic:
  a four-beat story shape, a callback from the closing beat to the opening one, banned selling
  registers, dashes barred as punctuation, a 200-280 word band, and every figure traced to
  `career_facts.yaml`. The house spec it enforces lives in `profile/06-cover-letter-notes.md`.
  *Hypothesis: a rule stated in a prompt is followed most of the time; a rule that exits non-zero is followed every time.*

- ✅ **Research as a precondition, not a suggestion** — `cover-letter` cannot draft until the
  `company-research` output exists, and the letter must share distinctive vocabulary with it.
  Built after a letter passed every style check on a company whose research had never been run,
  which made the "reference something specific about them" rule decoration.
  *Hypothesis: requiring the input artefact catches the skipped step, and requiring lexical overlap catches the model writing from its own memory instead; together they are a citation check that costs no model call.*

- ✅ **Failure-mode taxonomy** — `docs/FAILURE-MODES.md`, written from two weeks of real
  corrections. Of twelve repeat failures, one was a knowledge problem and eleven were structural.
  The file exists to stop the reflex of answering every correction with another rule.
  *Hypothesis: an agent that appends a rule per correction converges on a spec that is a memory test; fixing the cause is what makes the spec get shorter over time.*

- ✅ **The Reviewer is a step, not a suggestion** — a draft that has passed every mechanical
  check but has never been read by the fresh-context Reviewer is still unfinished, and the turn
  will not end. The receipt is the critique itself: a one-word note is refused, and editing the
  draft afterwards invalidates it, because the Reviewer is only useful on the text that will
  actually be sent. It cannot prove the Reviewer ran; it does mean nobody can call a draft
  finished while nothing has been filed.
  *Hypothesis: mechanical checks bound the floor and the faults that cost the most rounds are
  the ones no script can see, so the judgment layer is the one that most needed to stop being
  optional.*

- ✅ **CV house spec, split the way the letter spec already is** — `profile/08-cv-notes.md`
  carries the universal rules above the line and **YOURS** sections below it;
  `templates/resume.css` and `templates/resume.html` are the design system, linked and never
  pasted; `scripts/check-resume.sh` enforces the mechanical half with an `--all` sweep. The CV
  side had none of this, so every session re-derived the layout and the content rules from
  whatever CV was lying around.
  *Hypothesis: a spec written in prose is re-implemented from the description every time, so
  the drift is structural; a design asset the agent links cannot be got wrong, and it retires
  the checks that only existed to catch the re-implementation.*

- ✅ **Gates that run themselves** — writing a draft under `applications/` or `data/drafts/`
  triggers the learned rules, the letter checker and the honesty gate automatically, and the
  turn cannot end while a draft has never passed or a correction is unresolved. The checks were
  always there; what changed is that running them stopped being a step a model could skip. They
  live in `gates/` with the hooks as thin adapters, so the guarantees survive Lucy running
  outside Claude Code. Skips rather than blocks when a gate cannot run, and stops blocking after
  three refusals.
  *Hypothesis: a check that something has to remember to run is a promise, not a guarantee; the
  same check triggered by the write is what makes the difference between an agent that intends
  to close a loop and one that cannot leave it open.*

- ✅ **The correction loop** — a correction you make on a draft is stored as a standing rule
  in your own `profile/learned-rules.yaml`, then read back before every draft and enforced
  after it. A `UserPromptSubmit` hook notices correction-shaped language and reminds the agent
  to ask the one question that gates the whole thing: one-off, or from now on? Nothing is
  inferred, every learned rule is a line you can read and delete, and 14 mutation tests prove
  each check both fires and stays quiet. Rationale in `docs/DESIGN.md`; the skill is `learn`.
  Built, tested end to end, and not yet worn in by real use: whether the hook's phrase list
  catches real corrections is only knowable from watching it miss some.
  *Hypothesis: nobody can state their writing rules up front, because they discover them by
  rejecting drafts; a profile that cannot grow after setup stays as thin as the day setup ran,
  and the agent looks like it is forgetting when in fact it was never told.*

---

## Now

- ⬜ **Get it used by people who are not the owner.** The whole spec so far was paid for by one
  person dogfooding it on his own job search. That is the right way to find the rules and the wrong
  way to know which of them generalise. Before any further polish: put it in a handful of real
  hands, watch where a stranger's first run breaks, and treat what they correct as the same kind of
  signal the owner's corrections were.
  *Hypothesis: a tool tuned by one user against his own taste cannot tell which of its rules are
  universal and which are his; only a second user can, and that answer changes what ships.*

- 🔨 **Finish the core loop** — get discovery → fit → tailored CV and cover letter working
  end-to-end on a first real role, with the honesty gate passing on real output. In progress; not yet proven end-to-end.
  *Hypothesis: every other feature depends on the discovery→tailored-CV loop working end-to-end on real data first.*

- 🔨 **Public web page** — the project's front door: an explainer/landing page (`docs/index.html`)
  that shows what Lucy is and why it's built this way. Being built and polished in a parallel session.
  *Hypothesis: an open-source agent is only as credible as its front door; a clear explainer page is what turns a passing reader into someone who tries it.*

- 🔨 **Try-it demo** — an interactive page (`docs/try.html`) that lets someone watch Lucy run in
  ~30 seconds without installing anything. Under construction alongside the web page.
  *Hypothesis: letting someone see Lucy run in 30 seconds without installing anything bridges the gap between "read about it" and "use it."*

- 🔨 **Degrade gracefully off the happy path** — the first real-world run (a live Ashby role from
  a restricted-network session) surfaced where a stranger's first run actually breaks: JD fetch
  fails on JS-only ATS pages → paste-the-JD fallback (`data/jd/`, never reconstruct from search
  snippets); session missing the profile/facts → preflight stop instead of silent improvisation
  (plus `scripts/sync-private.sh`, which the private-repo docs referenced but which didn't exist);
  missing LaTeX/poppler → HTML+Chromium render fallback; Reviewer unspawnable → hard stop, not
  self-review; and written claims now carry their scope ("live in one pilot market", not "live in
  production") — a Reviewer rule, since the code gate can't catch true-but-unscoped.
  *Hypothesis: launch visitors run Lucy in hostile environments — blocked networks, missing tools,
  half-set-up clones — so the first-run experience is decided by failure handling, not the happy path.*

---

## Next

---

## Later

- ⬜ **Calibration loop** — feed real application outcomes back into the scoring rubric so it improves over time.
  *Hypothesis: a system that learns from which applications actually convert will outperform a static, hand-tuned rubric over time.*

- ⬜ **Outcome metrics** — measure the full funnel: applications→screens, screens→interviews,
  interviews→offers, and whether a warm intro changed conversion.
  *Hypothesis: you can't improve what you don't measure; tracking the full funnel is how we prove Lucy works, not just runs.*

- ⬜ **Guided onboarding** — a setup conversation that replaces hand-editing config files.
  *Hypothesis: hand-editing config is the scariest barrier; a guided setup conversation makes Lucy usable by non-technical people.*

- ⬜ **ATS auto-detect for the watchlist** — give Lucy plain company names and a helper script probes
  each ATS API (and falls back to scanning the careers page) to fill in the `ats:token` entries itself.
  *Hypothesis: hand-looking-up ATS handles is the most tedious step of watchlist building; automating it removes the last excuse not to track 50 companies instead of 10.*

- ⬜ **Contrast-based rubric calibration** — during setup, ask for 2–3 strong-fit postings *and* 1–2
  close-but-not-quite ones, and infer negative signals from the contrast; complements the outcome-based
  calibration loop above.
  *Hypothesis: near-miss examples encode what "looks right but isn't" better than any hand-written rule, because the user already knows it when they see it.*

- ⬜ **Morning email digest** — deliver the day's apply-first roles to the inbox via a scheduled
  overnight run (on an API key, to protect interactive quota) instead of writing a file.
  *Hypothesis: an agent that shows up in your inbox feels categorically different from a script that writes a file.*

- ⬜ **GTM positioning: "own your job search, don't rent it"** — sharpen the ownership wedge
  (your data, your logic, your machine) against SaaS job tools.
  *Hypothesis: the ownership angle (your data, your logic, your machine) is a differentiated wedge against SaaS job tools and matches where the market is heading.*

---

## Parked

- ⏸️ **Mock-interviewer** — live spoken practice that scores delivery, not just content.
  *Hypothesis: delivery matters as much as content in interviews — but this is a second product, so it waits until the core loop is proven.*

- ⏸️ **Hosted web app** — a multi-user, hosted version of Lucy.
  *Hypothesis: a multi-user product is the eventual path, but building it on an unfinished single-user loop is building the second floor before the first.*

---

This roadmap deliberately under-claims. An item is only "Shipped" when it works, not when the code
merely exists — and the core loop stays "in progress" until it runs end-to-end on a real role. If
anything here reads as done that isn't yet, treat this line as the correction.
