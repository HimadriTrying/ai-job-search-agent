---
name: submit
description: Fill a real application form from the tailored documents and answer bank, show a full review, and submit ONLY behind two independent human locks. On demand, human-gated. Never auto-invoked.
invocation: user
---

# submit — the human-gated frontier

## Precedent
Fills a real application form and stops at the submit line — the stage most systems leave
entirely manual. The human
firmly in it.

## Non-negotiable safeguards
- **Two independent locks**: an explicit `--submit` intent AND an in-session approval. One
  approval = exactly one application. **No batch path, ever.**
- **Visible browser** (e.g. Playwright): the user watches it fill the real form.
- **Never** handle passwords or captchas — pause, hand control back in the same window,
  resume without losing state.
- Screening-question routing:
  - Factual questions → answer bank / `career_facts.yaml` only. Blank + flagged if absent —
    no LLM guessing.
  - Consent / EEO → always pause for the human.
  - Free-text ("why us?") → draft grounded ONLY in career facts + this JD, run the
    **honesty gate**, tag `[AI-DRAFT]`, never auto-approve.

## Answer bank
A gitignored PII store (`data/answer_bank.yaml`, not committed) for reusable form answers.
Work-auth required; EEO opt-in and declinable.

The system stops at the moment of commitment. The human clicks submit.
