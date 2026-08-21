#!/bin/bash
# Stop hook — the turn does not end with the loop open.
#
# This is the difference between an agent that intends to close a loop and one that cannot
# leave it open. Two things it refuses to let past:
#
#   1. A draft that was written and never passed its gates. Not "was not checked recently":
#      never passed, in this session, since it was last written.
#   2. A correction the user made that was never resolved. Resolved means one of two things,
#      and the point is that the model has to have actually done one of them: the rule was
#      stored with learned_rules.py, or the user said it was a one-off and that was recorded.
#
# THE TRAP THIS AVOIDS
#
# A Stop hook that blocks on a condition the model cannot satisfy loops forever, burning quota
# on a fight the user never asked for and cannot see. Two guards: `stop_hook_active` means we
# are already inside a continuation and must not block again, and gates/session.py stops
# blocking after MAX_BLOCKS and reports instead. A gate that can never be satisfied is worse
# than one that can be skipped.
set -uo pipefail

INPUT="$(cat 2>/dev/null || true)"
[ -z "$INPUT" ] && exit 0
[ -n "${LUCY_GATES_OFF:-}" ] && exit 0

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
command -v python3 >/dev/null 2>&1 || exit 0

read -r -d '' PY <<'PYSRC' || true
import json, sys
try:
    d = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)
print(d.get("session_id", "nosession"))
print("active" if d.get("stop_hook_active") else "idle")
PYSRC

PARSED="$(printf '%s' "$INPUT" | python3 -c "$PY" 2>/dev/null || true)"
SESSION="$(printf '%s' "$PARSED" | sed -n '1p')"
ACTIVE="$(printf '%s' "$PARSED" | sed -n '2p')"

# Already continuing from a previous block: let it finish rather than risk a loop.
[ "$ACTIVE" = "active" ] && exit 0

ITEMS="$(python3 "$ROOT/gates/session.py" open-items --session "$SESSION" 2>/dev/null)"
CODE=$?
[ "$CODE" -eq 0 ] && exit 0
[ -z "$ITEMS" ] && exit 0

python3 "$ROOT/gates/session.py" record --session "$SESSION" --event blocked >/dev/null 2>&1 || true

{
  echo "Do not end here. This session has unfinished work:"
  printf '%s\n' "$ITEMS" | sed 's/^/  - /'
  echo
  echo "Finish it, or tell the user plainly what is unresolved and why. Do not present a"
  echo "draft as done when its gates never passed."
} >&2
exit 2
