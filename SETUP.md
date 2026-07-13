# Setup

## 1. Install Claude Code
```
npm install -g @anthropic-ai/claude-code
```
(Requires Node.js. See https://docs.claude.com/en/docs/claude-code/overview for current
install details.)

## 2. Open this repo in Claude Code
```
cd ai-job-search-orchestrator
claude
```
`CLAUDE.md` loads automatically — that's the orchestrator.

## 3. Build your profile FIRST (this is the whole game)
Say **"run setup"** or type `/setup`. The orchestrator interviews you and fills in
`profile/*.md` and `career_facts.yaml`. Expect to spend real time here across a few sessions —
profile depth drives output quality more than anything else.

Gather if you have them (none required to start):
- Your current CV
- LinkedIn → Settings → Data Export → **Connections** → save the CSV to `data/connections/`
- Past cover letters, references, diplomas

## 4. Then just talk to it
- "What roles are open that fit me?" → job-scout
- "Tailor my CV for this posting: <url>" → cv-tailor → reviewer → honesty gate
- "Who do I know at <company>?" → network-mapper
- "Prep me for my interview there" → company-research + interview-coach
- "What should I follow up on?" → tracker

## 5. Optional — turn on the scheduled scout
Add an `ANTHROPIC_API_KEY` repo secret and edit the watchlist. The workflow in
`.github/workflows/daily-scout.yml` runs a cheap discovery sweep on weekday mornings and
commits a digest. Keep the expensive, judgment-heavy work (tailoring, outreach) on demand so a
scheduled job never eats your interactive quota.

## Honesty gate (already wired)
Generative skills run `python honesty/verify.py <draft>` before showing you output. Install the
one dependency:
```
pip install pyyaml
```
