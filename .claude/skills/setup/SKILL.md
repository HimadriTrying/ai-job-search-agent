---
name: setup
description: Build the candidate profile from scratch through a guided interview. Run this first, before any other skill. Populates profile/*.md and career_facts.yaml.
invocation: user
---

# /setup — build your profile from scratch

The user has no materials yet. Your job is to interview them and produce their profile files.
Do not rush to fill everything in one pass; a rich profile is the highest-leverage thing in
this whole system, so it is worth several sessions.

## Before you start
Ask the user to gather, if they have them (none are required to begin):
- Their current CV / resume (any format)
- LinkedIn "Data Export → Connections" CSV → drop in `data/connections/` (feeds the network
  layer later; also gitignored as personal data)
- Any past cover letters, reference letters, diplomas

## The interview — run in this order, one theme at a time

1. **Career spine** → `profile/01-candidate-profile.md` and `career_facts.yaml`
   For each role: company, title, dates, real scope, specific projects, tools, and *only
   defensible* metrics. Push gently for numbers, but never invent one — if they can't defend
   it, it doesn't go in the facts. As you confirm each hard fact, write it to
   `career_facts.yaml` (this is the frozen truth the honesty gate uses).

2. **Energy audit** → `profile/02-behavioral-profile.md`
   Ask directly: what energized you, what drained you, what you want more of, what you won't
   do again. This shapes fit scoring more than the resume does. Suggest a free DISC or
   16Personalities if they want a working-style section.

3. **Voice** → `profile/03-writing-style.md`
   Ask for 1-2 paragraphs of their real writing. Extract do's/don'ts. This is what stops
   later drafts sounding like a language model.

4. **Rubric** → `profile/04-job-evaluation.md`
   Walk them through the knobs. Enforce the two design rules: mostly penalties, and
   **`min_seniority` drops below Senior** (inverted from the usual junior filter). Fill the
   YAML block with their real constraints (location, comp floor, exclusions).

5. **CV source + STAR bank** → `profile/05-cv-source.md`, `profile/07-interview-prep.md`
   The uncut CV content, and 6-10 real STAR stories covering the Staff/Group-level probes
   (direction-setting, influence without authority, a hard trade-off, an owned failure, a
   cross-team decision, an AI/tech-depth story).

## Rules
- **Never fabricate on the user's behalf.** If they can't substantiate a metric or skill,
  leave it out. The whole system's integrity rests on `career_facts.yaml` being true.
- Write incrementally to the files as facts are confirmed; don't hold everything in context.
- End each session by telling the user which files are still thin and what to bring next.

## Optional: Lenny's Product Skills (read-and-distill, don't bulk-install)
A subset of https://github.com/RefoundAI/lenny-skills is useful *as source material* for the
profile — read them once, distill into the user's own words, don't leave 86 PM-operating
skills installed and polluting agent triggering. Relevant ones for a Senior/Lead/Staff/Group
+ AI-builder target: `career-transitions`, `written-communication`, `defining-product-vision`,
`stakeholder-alignment`, `systems-thinking`, `evaluating-trade-offs`, `ai-product-strategy`,
`building-with-llms`, `ai-evals`. The hiring-side ones (`evaluating-candidates`,
`conducting-interviews`, `writing-job-descriptions`) are installed as *active* skills for the
Interview Coach — see that skill.
