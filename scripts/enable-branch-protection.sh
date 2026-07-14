#!/usr/bin/env bash
#
# enable-branch-protection.sh
#
# Locks down `main` so nobody (not even a direct push) can change this repo,
# and therefore the live web app deployed from it, without a reviewed PR that
# the CODEOWNERS owner has approved. Run this once.
#
# Safe to commit: contains NO personal data or tokens.
#
# What it turns on for `main`:
#   - Pull request required before merging (no direct pushes)
#   - At least 1 approving review
#   - Review must come from a CODEOWNERS owner
#   - Stale approvals dismissed when new commits are pushed
#   - Rules apply to admins too
#   - Force-pushes and branch deletion blocked
#
# Usage:
#   gh auth login          # once, if you use the GitHub CLI (recommended)
#   ./scripts/enable-branch-protection.sh
#
# Or without gh, export a token that has "repo" (admin) scope:
#   GITHUB_TOKEN=ghp_xxx ./scripts/enable-branch-protection.sh

set -euo pipefail

BRANCH="${BRANCH:-main}"

# Derive owner/repo from the origin remote.
remote_url="$(git config --get remote.origin.url)"
slug="$(printf '%s' "$remote_url" | sed -E 's#(git@github\.com:|https://github\.com/)##; s#\.git$##')"
OWNER="${slug%%/*}"
REPO="${slug##*/}"

if [ -z "$OWNER" ] || [ -z "$REPO" ]; then
  echo "Could not parse owner/repo from remote: $remote_url" >&2
  exit 1
fi

echo "Protecting $OWNER/$REPO branch '$BRANCH'..."

read -r -d '' PAYLOAD <<'JSON' || true
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

if command -v gh >/dev/null 2>&1; then
  printf '%s' "$PAYLOAD" | gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "/repos/$OWNER/$REPO/branches/$BRANCH/protection" \
    --input -
elif [ -n "${GITHUB_TOKEN:-}" ]; then
  curl -fsSL \
    -X PUT \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/$OWNER/$REPO/branches/$BRANCH/protection" \
    -d "$PAYLOAD"
else
  echo "Need either the GitHub CLI (gh) authenticated, or GITHUB_TOKEN set." >&2
  echo "Install: https://cli.github.com/  then: gh auth login" >&2
  exit 1
fi

echo
echo "Done. '$BRANCH' now requires a code-owner-approved PR to change."
