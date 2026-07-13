---
name: network-mapper
description: Find warm-intro paths into a target company from the user's own LinkedIn connections export. First-degree from the CSV; second-degree via enrichment + human-in-the-loop. No scraping. Scheduled weekly or on demand.
invocation: auto
---

# network-mapper — the gap nobody else builds

## Legal stance
LinkedIn blocks automation and litigates scraping. This skill uses **only the user's own
data**: LinkedIn Settings → Data Export → Connections → CSV in `data/connections/`. No
scraping, no ToS violation.

## First-degree (fully automatable today)
1. Parse the connections CSV.
2. Given a target company, find who in the network works (or worked) there.
3. Rank by relationship strength signals available in the export (connection date, shared
   context if present).

## Second-degree (the genuinely hard part — optimise the human step, don't fake it)
The export is first-degree only. Options, in order of preference:
- **Enrich** first-degree connections' current employers (Harmonic `enrich_person`, or
  Apollo/Hunter via API) and reason about who is *likely* to know someone relevant.
- **Ask** — draft a message for the user to send a first-degree contact requesting an intro.
  Often the export can't prove the second-degree link, so make the human ask efficient rather
  than eliminating it.

## Output
For each target role: warm-intro paths found, ranked, each with a suggested next action.
Hands off to `outreach-drafter`. Scheduled weekly (network changes slowly) or on demand.
