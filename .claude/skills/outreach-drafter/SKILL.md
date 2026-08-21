---
name: outreach-drafter
description: Write a personalized intro-request or outreach message for a specific warm path. Grounded only in real facts; runs the honesty gate. On demand — tone needs human judgment.
invocation: user
---

# outreach-drafter

## Precedent / mapping
The warm-intro half of the gap; Lenny's `finding-mentors-sponsors` reframed as the
warm-intro problem.

## Inputs
A specific path from `network-mapper`, `career_facts.yaml`, `profile/03-writing-style.md`,
the target role.

## Flow
1. Draft a short, specific message — reference the real connection, the real role, one true
   reason it fits. No flattery padding.
2. **Honesty gate** on the draft (it asserts facts about the user).
3. Present 1-2 variants. The user sends it — never you.

Keep it human. A generic "I'd love to connect" performs worse than nothing.

## The user's own rules
Read them before drafting and check the draft against them afterwards:

```bash
python scripts/learned_rules.py brief --scope outreach
python scripts/learned_rules.py check <draft> --scope outreach
```

Outreach is where a standing "never say that" is most likely to have been stated and most
costly to forget, because the message goes to a real person in the user's own network. If
they correct a draft, run `learn` before moving on.
