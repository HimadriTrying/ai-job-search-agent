#!/usr/bin/env bash
# Claude Code PostToolUse hook — the honesty gate, enforced by machinery.
#
# Fires after every Write/Edit. If the file is an outbound document under
# applications/, it runs honesty/verify.py on it. On a gate failure the findings
# go back to Claude on stderr (exit 2), so the document gets fixed in the same
# turn — no reliance on the skill remembering to run the gate.
#
# verify.py is deliberately conservative: it flags for human review rather than
# silently passing, so it produces known false positives (the candidate's own
# name, section headers, public tool names). Findings a human has reviewed and
# accepted live in honesty/accepted.txt (gitignored — personal data; see
# honesty/accepted.example.txt). A finding matching an accepted phrase is
# dropped; anything new still fails loudly.
#
# Wired up in .claude/settings.json. Safe on forks: if the facts file or the
# verifier is missing, the hook stays silent rather than blocking work.
set -u

payload=$(cat)
file=$(printf '%s' "$payload" | python3 -c \
  "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" \
  2>/dev/null) || exit 0

[ -z "$file" ] && exit 0

# Only outbound documents in the formats verify.py understands.
case "$file" in
  */applications/*.md|*/applications/*.txt|*/applications/*.tex) ;;
  *) exit 0 ;;
esac

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/..}" || exit 0

# Fork-friendly: no verifier or no frozen facts -> nothing to enforce yet.
[ -f honesty/verify.py ] && [ -f career_facts.yaml ] || exit 0

out=$(python3 honesty/verify.py "$file" 2>&1)
status=$?
[ "$status" -ne 1 ] && exit 0

# Keep only the warning lines, then drop any that match a human-accepted phrase.
warns=$(printf '%s\n' "$out" | grep '⚠' || true)
if [ -f honesty/accepted.txt ]; then
  accepted=$(grep -v '^[[:space:]]*#' honesty/accepted.txt | sed '/^[[:space:]]*$/d' || true)
  if [ -n "$accepted" ]; then
    warns=$(printf '%s\n' "$warns" | grep -viF "$accepted" || true)
  fi
fi

[ -z "$warns" ] && exit 0

{
  echo "HONESTY GATE (automatic hook) failed for: $file"
  echo ""
  printf '%s\n' "$warns"
  echo ""
  echo "Fix the document, not the facts (career_facts.yaml is frozen truth)."
  echo "If the human has reviewed a finding and confirmed it is NOT a fabrication,"
  echo "they can add the flagged phrase to honesty/accepted.txt."
} >&2
exit 2
