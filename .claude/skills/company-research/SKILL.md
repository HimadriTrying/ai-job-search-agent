---
name: company-research
description: Research a company before applying or interviewing — from a quick pre-application summary to a full interview-prep dossier (4-track web sweep). On demand, and MANDATORY at deep level once an interview process starts.
invocation: auto
---

# company-research

Two levels. Pick by stage:

- **Level 1 — quick scan** (pre-application, feeds `cover-letter` and the `job-scout`
  fit-check): the lightweight summary below.
- **Level 2 — deep dossier** (an interview process exists): the 4-track sweep below.
  **Gate rule: a process folder is not prep-ready until its dossier exists.** If the
  private repo is synced (`private/`), the canonical protocol lives at
  `private/processes/_company-research-protocol.md` — follow that version if present;
  this file is the public, generic mirror.

## Inputs
Company name / URL, the JD, web search — in English AND the company's home-market
language. Optionally Harmonic MCP (enrich_company) if connected.

## Level 1 output — quick scan
- What they do and how they make money (plain language)
- Recent news / trajectory / funding or earnings signal
- Culture signals (from JD language, reviews, public posts)
- **JD decoding** (hiring-side inversion): read `writing-job-descriptions` logic to tell what
  a requirement *really* signals vs. boilerplate — what they're actually anxious about.
- 3-5 things to reference in a cover letter or interview

## Level 2 — deep dossier (4-track parallel web sweep)

Fan out four research tracks (parallel agents if available), each returning dated
facts with source URLs:

1. **Business trajectory** — history, funding, ownership, growth datapoints over time
   (AUM/revenue/users), headcount, layoffs/expansions, awards, leadership changes,
   strategy statements, negative coverage.
2. **Products & releases** — product ladder evolution, launch dates and volumes,
   partnerships, pricing, app-store presence + review themes (PM-interview gold),
   tech stack from job ads, category/market context.
3. **Communications** — the company's own channels (podcast/blog/webinars), every
   findable exec interview 2–3 years back with each person's RECURRING MESSAGES
   synthesized, PR coverage arc by year, last-6-months news (freshest = best in the room).
4. **Retrospective counterpart** — the candidate's current/former employer's PUBLIC
   trajectory, so any contrast narrative rests entirely on citable sources.

**Dossier structure** (one file per process, beside the role-prep notes; in the synced
private repo: `private/processes/<company>/company-research.md`):
corrections-vs-prior-beliefs → timeline → business performance table → products &
releases → competitive context → communications layer → people (public layer) →
employer retrospective → interview ammo (talking points, smart questions, a speakable
60-second company story) → morning-of verification list.

**Rules:**
- **Public-cover discipline**: only publicly sourced facts enter the dossier → everything
  in it is safe to say aloud. Mark facts that independently confirm something known
  from confidential sources as **[PUBLIC COVER]**; confidential material never migrates in.
- **Namesake check** first — verify the name isn't shared with an unrelated firm before
  trusting aggregators.
- Single-source numbers are flagged "don't assert," never averaged. Registry > press >
  review portals > data vendors.
- Refresh before every human round; keep a short list of volatile facts to re-verify
  the morning of.

Feeds `cover-letter`, `interview-coach`, and the fit-check in `job-scout`.
