# AI Job Search Agent

**Meet Lucy — one agent you talk to, across the entire job-search funnel — from discovering a
role to walking into the interview holding the hiring manager's own playbook.**

Job hunting is a funnel: discover roles → judge fit → tailor documents → **find a warm path
in** → apply → track → interview → offer → negotiate. Most tools automate one stage and leave
you to stitch the rest together by hand. Lucy is a single conversational orchestrator that
manages the whole funnel, refuses to fabricate anything about you, and always stops before
committing you to anything.

> **Status:** scaffolded and validated. The orchestrator, the code-enforced honesty gate, and
> the twelve specialist skills are in place. You fill in your profile — the part that
> determines output quality — and the system does the rest.

## What it does

You describe what you need in plain language. The orchestrator decides which specialists to
run and in what order, then synthesises the result. Twelve specialists cover the funnel:

- **Discovery** — sweeps public ATS APIs (Greenhouse, Lever, Ashby, SmartRecruiters), drops
  out-of-band roles *before* spending any model call, and scores survivors with a penalty-first
  rubric that filters hard instead of flattering everything.
- **Tailored documents** — a drafter writes your CV and cover letter, a fresh-context reviewer
  critiques them, the drafter revises, and the output is compiled and visually checked.
- **The warm-intro layer** — the stage almost nothing else touches. Works from *your own*
  LinkedIn connections export to find a real path into a target company, and drafts the outreach.
- **Interview prep from the other side of the table** — the coach is fed the hiring-side
  playbook (how interviewers evaluate, structure loops, and write the JD) so it prepares you
  from the interviewer's seat.
- **Tracking, upskilling, and negotiation** — active follow-up nudges, a skill-gap learning
  plan, and offer strategy at the end.

## Three ideas that define it

1. **A conversational orchestrator, not a command list.** Lucy (`CLAUDE.md`) routes to
   specialists. Nothing to memorise; you just say what you want.
2. **Honesty enforced in code, not prompted.** Every outbound document is checked against a
   frozen `career_facts.yaml` by `honesty/verify.py` before it can leave the system. Invent an
   employer, a credential, or a metric and the build fails loudly. A promise you can verify
   beats one you cannot.
3. **The human commits, never the agent.** It automates everything up to applying, reaching
   out, or accepting — then hands control back. The submit path enforces this with two
   independent locks.

## Built for senior roles
Tuned for Senior / Lead / Staff / Group PM and AI-product-builder roles: the seniority filter
is a *floor* that drops anything below Senior, the inverse of the usual junior-candidate filter.

## The build is itself the portfolio
This is a multi-agent system on Claude Code — skills, subagent orchestration, an evals-style
honesty gate, scheduled headless runs. For an AI-product role, the repo is the work sample.

## Layout
```
CLAUDE.md              # the orchestrator brain (always loaded)
career_facts.yaml      # frozen source of truth for the honesty gate (private; see .example)
honesty/verify.py      # the code-enforced honesty gate
profile/               # your brain — fill this first (see profile/00-README.md)
.claude/skills/        # the twelve specialists (auto-triggerable + /name invocable)
.claude/agents/        # the fresh-context reviewer subagent
data/                  # tracker (funnel state) + digests + your connections export (private)
.github/workflows/     # the scheduled "runs while you sleep" scout
docs/DESIGN.md         # the architecture rationale
```
Your personal files (`career_facts.yaml`, filled `profile/*.md`, `data/`) are gitignored by
default; the committed `*.example` versions keep the repo forkable without leaking anything.

## Start here
Open the repo in **Claude Code** and say *"run setup"* (or `/setup`). Lucy takes it from there. See `SETUP.md`.

## Prior art & acknowledgements
This system was designed after studying the best public job-search automation available, and it
owes real debts. Several open projects proved out ideas that this one adapts and builds on:
[Scotty Peterson's funnel write-up](https://www.scottypeterson.net/blog/job-hunting-is-a-funnel-problem)
on discovery and penalty-first scoring; **Mads Lorentzen's** [`ai-job-search`](https://github.com/MadsLorentzen/ai-job-search)
(MIT) on the drafter–reviewer pattern and document verification; and **Aravind Pranav's**
[`job-agent`](https://github.com/aravindpranav/job-agent) (MIT) on enforcing honesty in code and
gating submission behind human approval. Interview and career-planning framing draws on
[Lenny's Product Skills](https://github.com/RefoundAI/lenny-skills) (MIT). Where this system goes
its own way — the conversational orchestrator over the whole funnel, the warm-intro network
layer, and preparing from the hiring side of the table — it says so. MIT licensed.
