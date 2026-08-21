#!/bin/bash
# PostToolUse hook — makes checking a consequence of writing, not a step after it.
#
# The checks in this repo already exit non-zero. The weakness was never the checks: it was that
# running them was a step the model performed, and a skipped step leaves no trace, so a
# document nobody checked looks exactly like one that passed. That is how a cover letter went
# out green on a company whose research had never been run.
#
# This is a thin adapter. Every decision lives in gates/run.py so the guarantees survive Lucy
# running outside Claude Code, where this hook does not exist. Adapters are disposable; gates
# are not.
#
# Exit 2 feeds the failure back to the session as a blocking correction rather than output that
# scrolls past. Same mechanism as scripts/check-copy-style.sh.
set -uo pipefail

INPUT="$(cat 2>/dev/null || true)"
[ -z "$INPUT" ] && exit 0

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
command -v python3 >/dev/null 2>&1 || exit 0

read -r -d '' PY <<'PYSRC' || true
import json, sys
try:
    d = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)
ti = d.get("tool_input") or {}
print(d.get("session_id", "nosession"))
print(ti.get("file_path") or ti.get("path") or "")
PYSRC

PARSED="$(printf '%s' "$INPUT" | python3 -c "$PY" 2>/dev/null || true)"
SESSION="$(printf '%s' "$PARSED" | sed -n '1p')"
FILE="$(printf '%s' "$PARSED" | sed -n '2p')"
[ -z "${FILE:-}" ] && exit 0
[ -f "$FILE" ] || exit 0

OUT="$(python3 "$ROOT/gates/run.py" "$FILE" --quiet 2>&1)"
CODE=$?

# Nothing to say means this file is not a document the gates cover. Silence is the common case
# and it has to stay free: this hook runs on every single edit.
[ -z "$OUT" ] && [ "$CODE" -eq 0 ] && exit 0

if [ "$CODE" -ne 0 ]; then
  python3 "$ROOT/gates/session.py" record --session "$SESSION" \
      --event draft-failed --path "$FILE" >/dev/null 2>&1 || true
  printf '%s\n' "$OUT" >&2
  exit 2
fi

python3 "$ROOT/gates/session.py" record --session "$SESSION" \
    --event draft-passed --path "$FILE" >/dev/null 2>&1 || true
exit 0
