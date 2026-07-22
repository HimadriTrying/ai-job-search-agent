# Role-prep context — per-process structure (TEMPLATE)

> **Where the real files live:** in your **private companion repo**, wired in by
> `scripts/sync-private.sh` — never in this public repo. The `processes/` path here is
> gitignored **and** hard-blocked by the pre-commit guard. Design principle: *the tool is
> public; the person is private.* Everything you and the agent produce together — CVs,
> prep notes, questions, narratives — belongs to you alone.
>
> You will often run **several interview processes in parallel**, each at a different
> stage. One folder per company keeps them separate; one shared file holds what travels
> across all of them. Processes are **airgapped**: the agent never mentions one company's
> process inside another's.

## Layout

```
processes/
  _shared.md                 # cross-process: who you are for interviewers, flagship
                             # stories with real metrics, definitions bank, departure
                             # narrative, working agreements, standing confidentiality
  <company-a>/role-prep.md   # everything specific to company A's process
  <company-b>/role-prep.md   # …company B, at whatever different stage it's in
```

## `_shared.md` sections

- **Agent behaviors** for prep mode (coach-not-flatterer, mock interviewer, term tutor)
- **Candidate framing** — positioning, career-path story, counter to your weakest pattern
- **Flagship-story knowledge base** — deep detail of your best story; label measured vs
  estimated metrics
- **Definitions bank** — every technical/regulatory term, plain-English, grows per session
- **Departure narrative** — the rehearsed true story + explicit never-say list; the
  stay-condition line is adapted per company in each process file
- **Working agreements** — how you and the agent run prep sessions
- **Standing confidentiality rules** — apply to every process, absolute

## `<company>/role-prep.md` sections

- **A. Target company** — verified facts (re-verify before each round), your specific
  strategic angle, the role(s) in play
- **B. The people** — each interviewer: what their round tests, incentives, watch-fors
- **C. Process status** — stage log with dates; update after every touchpoint
- **D. Question banks** — what to ask whom; intel still to extract
- **E. Still to prepare** — concrete actions, highest-ROI first
- **F. Process-specific confidentiality** — sources never revealed, facts never
  volunteered, in this process specifically
