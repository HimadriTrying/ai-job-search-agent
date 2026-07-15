# Roadmap

Where Lucy is, and where she's going. This roadmap tracks the whole job-search funnel —
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

---

## Now

- 🔨 **Finish the core loop** — get discovery → fit → tailored CV and cover letter working
  end-to-end on a first real role, with the honesty gate passing on real output. In progress; not yet proven end-to-end.
  *Hypothesis: every other feature depends on the discovery→tailored-CV loop working end-to-end on real data first.*

- 🔨 **Public web page** — the project's front door: an explainer/landing page (`docs/index.html`)
  that shows what Lucy is and why she's built this way. Being built and polished in a parallel session.
  *Hypothesis: an open-source agent is only as credible as its front door; a clear explainer page is what turns a passing reader into someone who tries it.*

- 🔨 **Try-it demo** — an interactive page (`docs/try.html`) that lets someone watch Lucy run in
  ~30 seconds without installing anything. Under construction alongside the web page.
  *Hypothesis: letting someone see Lucy run in 30 seconds without installing anything bridges the gap between "read about it" and "use it."*

---

## Next

- ⬜ **Network mapper** — warm-intro paths into a target company, built from your own LinkedIn
  connections export. Scaffolded as a skill; not yet validated on real connection data.
  *Hypothesis: a warm intro changes conversion more than a perfect CV, so surfacing who you already know is the highest-leverage unbuilt piece.*

- ⬜ **Answer bank** — a validated, honesty-checked store for the repetitive questions application
  forms ask, so they're answered once and reused.
  *Hypothesis: repetitive application questions are pure friction; a validated, honesty-checked answer store removes it without risking fabrication.*

- ⬜ **Launch video (15–20s explainer)** — a short film showing Lucy actually working.
  *Hypothesis: a short, honest film showing Lucy actually working communicates the product faster than any copy, and doubles as the launch asset.*

- ⬜ **Workday + Gem fetchers** — extend `scout/ats.py` beyond Greenhouse/Lever/Ashby/SmartRecruiters
  to Workday (server-side pre-filtering + pagination) and Gem, plus a per-company seniority override
  for companies with non-standard title ladders (e.g. "Lead" where others say "Director").
  Workday pattern proven in [strategic-copilot](https://github.com/jordanmilner-lgtm/strategic-copilot).
  *Hypothesis: Workday is where enterprise and F500 postings live; without it the daily sweep is blind to a large share of senior roles.*

- ⬜ **"Business pain" line in scout digests** — for every apply-first role, one sentence on what
  problem the company is trying to solve with this hire, carried from scoring into the digest.
  *Hypothesis: the cover-letter rule says open with the company's problem; if discovery already names that problem, every downstream document starts from a running head start.*

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
