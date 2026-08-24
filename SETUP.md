# Setup

## 1. Install Claude Code and get the repo

```bash
npm install -g @anthropic-ai/claude-code
git clone https://github.com/HimadriTrying/ai-job-search-agent.git
cd ai-job-search-agent
pip install pyyaml
```

Node is needed for Claude Code, Python 3 for the honesty gate. You also need a Claude Pro or
Max subscription, or an Anthropic API key. See
https://docs.claude.com/en/docs/claude-code/overview for current install details.

## 2. Open it

```bash
claude
```

`CLAUDE.md` loads automatically. That is the orchestrator: you talk to it in plain language and
it routes to the right specialist.

## 3. Get a profile in place

**The profile is the whole game.** Output quality tracks its depth more than anything else,
including which model you run. There are two ways in, and they are not exclusive.

**Fast, if you have already used the try page.** It can hand you a seed built from the CV you
pasted there:

```bash
python scripts/import-seed.py ~/Downloads/lucy-profile-seed.json
```

That writes `career_facts.yaml` and `profile/05-cv-source.md` so you skip the longest part of
the interview. **Read `career_facts.yaml` before you trust it.** A model read it out of your CV,
so a date can be wrong or a metric can sit under the wrong employer, and those become the facts
the honesty gate checks every document against. It is stamped `verified: false` and the gate
warns on every run until you have read it and set `verified: true`.

**Thorough, and still worth doing.** Say **"run setup"** or type `/setup`. The orchestrator
interviews you and fills in the rest: how you work, your voice, your evaluation rubric, your
STAR stories. Expect real time here across a few sessions. The seed covers facts; this covers
everything that makes the output sound like you.

Gather if you have them, none required to begin:

- Your current CV
- LinkedIn → Settings → Data Export → **Connections** → save the CSV to `data/connections/`
- Past cover letters, references, diplomas

## 4. Then just talk to it

- "What roles are open that fit me?" → job-scout
- "Tailor my CV for this posting: <url>" → cv-tailor → Reviewer → honesty gate
- "Who do I know at <company>?" → network-mapper
- "Prep me for my interview there" → company-research + interview-coach
- "What should I follow up on?" → tracker

Correct it freely. When you push back on how something is written, it asks whether that is a
one-off or a standing rule, and a standing rule gets written into your own profile so the same
correction does not come back next week.

## 5. Optional: the scheduled scout

Add an `ANTHROPIC_API_KEY` repo secret and edit the watchlist.
`.github/workflows/daily-scout.yml` runs a cheap discovery sweep on weekday mornings and commits
a digest. It refuses to run in a public repository, because digests name the companies you are
targeting, so this one needs a private copy of the repo.

Keep the expensive, judgment-heavy work (tailoring, outreach) on demand, so a scheduled job
never eats your interactive quota.
