# Setup

## 1. Install Claude Code
```
npm install -g @anthropic-ai/claude-code
```
(Requires Node.js. See https://docs.claude.com/en/docs/claude-code/overview for current
install details.)

## 2. Open this repo in Claude Code
```
cd ai-job-search-agent
claude
```
`CLAUDE.md` loads automatically — that's the orchestrator.

## 3. Check the install works (30 seconds, no network, no profile)
Before you spend an hour on the setup interview, confirm the machinery runs. All three
commands work offline against fixtures, so nothing here needs your data or a working
connection to any job board:

```bash
pip install pyyaml
python honesty/tests/test_verify.py                                    # the honesty gate
python .claude/skills/job-scout/tests/test_scout.py                    # discovery + scoring
cd .claude/skills/job-scout && python run.py --offline tests/fixtures/jobs.sample.json
```

The last one writes a real digest to `data/digests/YYYY-MM-DD.md`, sorted into apply-first,
worth-a-look, skipped and dropped, with the reason for every decision. That is the discovery
half of Lucy working end to end on sample data. If those pass, a later failure is your
config or your network, not the install.

## 4. Build your profile FIRST (this is the whole game)
Say **"run setup"** or type `/setup`. The orchestrator interviews you and fills in
`profile/*.md` and `career_facts.yaml`. Expect to spend real time here across a few sessions —
profile depth drives output quality more than anything else.

Gather if you have them (none required to start):
- Your current CV
- LinkedIn → Settings → Data Export → **Connections** → save the CSV to `data/connections/`
- Past cover letters, references, diplomas

## 5. Then just talk to it
- "What roles are open that fit me?" → job-scout
- "Tailor my CV for this posting: <url>" → cv-tailor → reviewer → honesty gate
- "Who do I know at <company>?" → network-mapper
- "Prep me for my interview there" → company-research + interview-coach
- "What should I follow up on?" → tracker

## 6. Optional — turn on the scheduled scout
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
