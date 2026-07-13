---
name: company-research
description: Summarize a company before applying or interviewing — what they do, culture, recent news, and what their JD really signals. On demand.
invocation: auto
---

# company-research

## Inputs
Company name / URL, the JD, web search. Optionally Harmonic MCP (enrich_company) if connected.

## Output
- What they do and how they make money (plain language)
- Recent news / trajectory / funding or earnings signal
- Culture signals (from JD language, reviews, public posts)
- **JD decoding** (hiring-side inversion): read `writing-job-descriptions` logic to tell what
  a requirement *really* signals vs. boilerplate — what they're actually anxious about.
- 3-5 things to reference in a cover letter or interview

Feeds `cover-letter`, `interview-coach`, and the fit-check in `job-scout`.
