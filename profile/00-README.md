# Your Profile — the agent's brain

**Fill these in before running any specialist.** The single biggest driver of output quality
is not prompt engineering — it is the depth of these files. A thin profile produces generic
applications; a detailed one produces genuinely tailored ones.

Build them in this order (this is also what the `/setup` skill walks you through):

1. `01-candidate-profile.md` — education, experience, skills, in *context*
2. `02-behavioral-profile.md` — how you work, and honest energy audit
3. `03-writing-style.md` — your voice, so drafts sound like you
4. `04-job-evaluation.md` — the scoring rubric (mostly penalties; seniority inverted)
5. `05-cv-source.md` — master CV content; also the raw material for `career_facts.yaml`
6. `06-cover-letter-notes.md` — angles, stories, things you refuse to say
7. `07-interview-prep.md` — STAR stories from real experience
8. `processes/<company>/role-prep.md` — *(one per live interview process; parallel
   processes are normal)* target company, interviewers, process status, confidentiality
   lines — plus `processes/_shared.md` for what travels across all processes. The most
   sensitive data in the system: gitignored, hard-blocked by the pre-commit guard, and
   stored durably in the **private companion repo** (see `scripts/sync-private.sh` and
   `profile/08-role-prep.example.md` for the structure).

**Dual purpose:** because you are building publicly while job-searching, an honest,
well-structured profile is also the *first artifact in the public repo* — the reasoning is
more interesting to read than the code. Redact anything private before publishing; keep the
structure and the thinking.

> Rule that governs all of these: describe what you *actually did* — specific projects,
> tools, responsibilities, measurable results — not job titles. "Built ML churn-prediction
> pipelines in Python/scikit-learn" beats "Python, machine learning" every time.
