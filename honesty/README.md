# The Honesty Gate

This is the difference between *promising* not to fabricate and *proving* it.

Instructing a model "never fabricate" in a prompt is a promise. This system enforces it in
**code** instead: every outbound document is checked against a frozen source of truth before
it can leave the system. A promise you can verify mechanically is worth more than one you
cannot. This directory is that gate.

## How it works
1. `career_facts.yaml` (repo root) is the frozen source of truth. You edit it only when your
   real history changes.
2. Any skill that produces an outbound document (`cv-tailor`, `cover-letter`,
   `outreach-drafter`, and the free-text path in `submit`) writes the draft to a file, then
   runs:
   ```bash
   python honesty/verify.py <draft-file> --target "<Company>" --job <jd-file>
   ```
   `--target` / `--job` declare the role the document responds to. A cover letter
   legitimately names the company it addresses and echoes the posting's own vocabulary —
   those are references, not claims about the candidate, and the gate treats them as such.
3. Exit code `0` = clean. Exit code `1` = a potential invented entity, credential, or metric
   was found. **The document is fixed, never the facts.**

## What it catches
- Employers / organisations that appear in neither your facts nor the declared target/JD
- Certification/degree claims with no backing credential
- Hard numbers (metrics, team sizes, percentages) with no basis in the facts. Numbers are
  **claim-scoped**: they may only come from fields that carry claims (employer metrics,
  scope, employment dates and tenures, education/certification years) — never from contact
  details, so a phone number can't quietly "support" a growth percentage
- **Misattribution**: a real metric moved to the wrong employer. In a sentence that names
  one known employer, a number must come from that employer's own record

## Tests
The gate's contract is encoded in `tests/test_verify.py` (fictional data, offline):
```bash
python honesty/tests/test_verify.py
```

## What it does *not* catch
Spin, tone, and overclaiming that uses only real facts. That is the job of the fresh-context
**Reviewer** subagent (`.claude/agents/reviewer.md`). Code catches invented facts; the
Reviewer catches framing. Run both.

## Why it's conservative
It flags for human review rather than silently rewriting. A false positive costs you ten
seconds; a false negative sends a lie to a hiring manager. The asymmetry justifies the bias.
