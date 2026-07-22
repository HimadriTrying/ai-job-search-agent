#!/usr/bin/env bash
#
# check-private.sh — refuse to commit private data into this public repo.
#
# This script is safe to commit: it contains NO personal data. It gets its list of
# private tokens (names, emails, employer names, …) from a gitignored file, `.private-guard`,
# so the token list itself never lands in the public repo.
#
# It does two things against the *staged* changes:
#   1. Hard-blocks the known private paths (career_facts.yaml, real profile/0X files, tracker,
#      connections, digests) even if force-added with `git add -f`.
#   2. Scans staged file *content* for any literal token listed in `.private-guard`.
#
# Wire it up once:  git config core.hooksPath .githooks
# Bypass in a genuine false positive:  git commit --no-verify   (use sparingly)

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

fail=0

# 1) Private paths that must never be committed (mirrors .gitignore; catches `git add -f`).
PRIVATE_PATHS_RE='^(career_facts\.yaml|profile/0[1-8]-[a-z0-9-]+\.md|data/tracker\.csv|data/connections/.+\.csv|data/digests/.+\.md|\.private-guard)$'
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if printf '%s\n' "$f" | grep -Eq "$PRIVATE_PATHS_RE"; then
    echo "🚫 BLOCKED path: '$f' is private and must never be committed to a public repo."
    fail=1
  fi
done < <(git diff --cached --name-only)

# 2) Scan staged content against literal tokens in .private-guard (gitignored).
guard=".private-guard"
if [ -f "$guard" ]; then
  patterns="$(grep -vE '^[[:space:]]*(#|$)' "$guard" || true)"
  if [ -n "$patterns" ]; then
    while IFS= read -r f; do
      [ -z "$f" ] && continue
      staged="$(git show ":$f" 2>/dev/null || true)"
      [ -z "$staged" ] && continue
      hits="$(printf '%s' "$staged" | grep -iFf <(printf '%s\n' "$patterns") | head -3 || true)"
      if [ -n "$hits" ]; then
        echo "🚫 BLOCKED content: '$f' contains private token(s):"
        printf '     %s\n' "$hits"
        fail=1
      fi
    done < <(git diff --cached --name-only --diff-filter=ACM)
  fi
fi

if [ "$fail" -ne 0 ]; then
  echo
  echo "Commit aborted to protect private data on this public repo."
  echo "If this is genuinely a false positive, review the file, then: git commit --no-verify"
  exit 1
fi
exit 0
