#!/bin/bash
# UserPromptSubmit hook — the event that starts the correction loop.
#
# WHY A HOOK AND NOT A PROMPT INSTRUCTION
#
# There is no "the user rejected the draft" event to subscribe to. The closest real event is
# the user submitting a prompt, so that is what this listens on. It reads the prompt, and when
# it is shaped like a correction to generated writing ("don't say", "that's not my voice",
# "I told you already"), it prints a reminder that gets added to the session's context.
#
# The reminder is what makes the loop fire reliably. CLAUDE.md already carries the rule, but a
# rule near the top of a long session competes with everything since; a line injected at the
# moment of the correction does not.
#
# WHAT THIS IS NOT
#
# It is a nudge, not a guarantee. It cannot tell a correction from a passing remark, so it is
# deliberately conservative: a tight phrase list, and at most one nudge every 15 minutes so it
# never turns into nagging. Missing a correction costs one repeated correction. Firing on every
# message would cost the user's attention, which is worse — a nudge that always fires is a
# nudge that gets ignored, the same way a checker that is always red gets ignored.
#
# It never fails the prompt: any error exits 0 and the session continues untouched.
set -uo pipefail

INPUT="$(cat 2>/dev/null || true)"
[ -z "$INPUT" ] && exit 0

# Pull the prompt and session id out of the hook payload. Fall back to the raw text if the
# payload is not the shape we expect, so a contract change degrades to "slightly noisier"
# rather than "silently dead".
if command -v python3 >/dev/null 2>&1; then
  read -r -d '' PY <<'PYSRC' || true
import json, sys
try:
    d = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)
print(d.get("session_id", "nosession"))
print((d.get("prompt") or "").replace("\n", " ")[:2000])
PYSRC
  PARSED="$(printf '%s' "$INPUT" | python3 -c "$PY" 2>/dev/null || true)"
  SESSION="$(printf '%s' "$PARSED" | sed -n '1p')"
  PROMPT="$(printf '%s' "$PARSED" | sed -n '2p')"
else
  SESSION="nosession"
  PROMPT="$INPUT"
fi
[ -z "${PROMPT:-}" ] && exit 0

# Correction-shaped language. Deliberately tight: these are phrases people use when they are
# rejecting how something was written, not when they are asking for new work. Widen this list
# only after watching a real correction slip past it.
PATTERN='(do not|don.t|never|stop) (say|write|use|call|describe)'
PATTERN="$PATTERN"'|(that|this|it) (is|.s) not (my|the) (voice|tone|style|register)'
PATTERN="$PATTERN"'|(too|very) (salesy|generic|corporate|formal|wordy|long)'
PATTERN="$PATTERN"'|(i|we) (already )?(told|said to|asked) you'
PATTERN="$PATTERN"'|(you|it) (keep|keeps|kept) (doing|saying|writing|using)'
PATTERN="$PATTERN"'|(again|same (mistake|thing)) *[.!]?$'
PATTERN="$PATTERN"'|(from now on|going forward|every time)'
PATTERN="$PATTERN"'|(i|we) (hate|do not like|don.t like) (that|this|the) (word|phrase|line)'
PATTERN="$PATTERN"'|not what (i|we) asked'
PATTERN="$PATTERN"'|(reword|rewrite) (that|this|it)'

printf '%s' "$PROMPT" | grep -qiE "$PATTERN" || exit 0

# Rate limit: at most one nudge every 15 minutes per session.
MARKER="${TMPDIR:-/tmp}/lucy-correction-nudge-${SESSION}"
if [ -f "$MARKER" ]; then
  NOW=$(date +%s)
  THEN=$(stat -c %Y "$MARKER" 2>/dev/null || stat -f %m "$MARKER" 2>/dev/null || echo 0)
  [ $((NOW - THEN)) -lt 900 ] && exit 0
fi
touch "$MARKER" 2>/dev/null || true

cat <<'NUDGE'
[correction loop] That prompt reads like a correction to generated writing. Before you fix the
draft and move on: ask whether it is a one-off for this document or a standing rule. If it is
standing, run the `learn` skill and store it with scripts/learned_rules.py in THIS session, so
it is honoured next time instead of being corrected again. If it is a one-off, just fix the
draft and say nothing further. Do not infer the answer; one plain question is the whole gate.
NUDGE
exit 0
