---
name: tracker
description: Active application tracker and funnel measurement. Logs applications, surfaces follow-up nudges by elapsed time, connects roles to warm paths, and reports pipeline health. Scheduled (nudges) + on demand.
invocation: auto
---

# tracker — active, not passive

Most systems have a passive CSV. This one nudges and measures.

## State
`data/tracker.csv` — the durable memory of the funnel. On a fresh session, read it first to
answer "where are we".

## Responsibilities
- **Log** each application: company, role, stage, dates, warm-path (yes/no), source.
- **Nudge**: flag applications past a follow-up threshold (pure time logic — trivially cheap,
  safe to run scheduled).
- **Connect** roles to `network-mapper` output — is there a warm path not yet used?
- **Measure the funnel**: applications→screens, screens→interviews, interviews→offers. And
  the experiment worth running: does having a warm intro measurably change conversion?

## Stages
`identified → tailoring → applied → screen → interview → offer → closed(reason)`
