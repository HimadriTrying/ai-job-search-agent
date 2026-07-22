#!/usr/bin/env bash
#
# sync-private.sh — wire the private data repo into the tool repo.
#
# Lucy is a public tool; the person using her is private. All personal state
# (career_facts.yaml, real profile/, tracker, per-process role-prep) lives in a
# SEPARATE PRIVATE repo, cloned to ./private/ (gitignored here). This script
# clones/updates that repo and symlinks its files into the paths the skills
# expect — all of which are already gitignored and blocked by the pre-commit
# guard, so nothing private can leak into the public repo.
#
# Usage:
#   scripts/sync-private.sh [private-repo-url]
# Default URL can be pinned in .private-repo-url (gitignored, one line).

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

url="${1:-}"
[ -z "$url" ] && [ -f .private-repo-url ] && url="$(head -n1 .private-repo-url)"

if [ ! -d private/.git ]; then
  if [ -z "$url" ]; then
    echo "No ./private clone and no URL given."
    echo "Usage: scripts/sync-private.sh <private-repo-url>   (or put the URL in .private-repo-url)"
    exit 1
  fi
  git clone "$url" private
else
  git -C private pull --ff-only || echo "⚠️  could not pull ./private — continuing with local copy"
fi

# Symlink private files into the paths the skills expect. Only link what exists;
# never overwrite a real (non-symlink) file silently.
link() { # link <target-in-private> <path-in-tool-repo>
  src="private/$1" dst="$2"
  [ -e "$src" ] || return 0
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    echo "⚠️  $dst exists and is a real file — not touching it. Reconcile with private/$1 manually."
    return 0
  fi
  mkdir -p "$(dirname "$dst")"
  ln -sfn "$(pwd)/$src" "$dst"
  echo "   linked $dst -> $src"
}

echo "Linking private state into place:"
link career_facts.yaml            career_facts.yaml
for f in private/profile/0*.md; do
  [ -e "$f" ] || continue
  link "profile/$(basename "$f")" "profile/$(basename "$f")"
done
link data/tracker.csv             data/tracker.csv
link data/connections             data/connections
link data/digests                 data/digests
link applications                 applications
link processes                    processes
link .private-guard               .private-guard

# Make sure the pre-commit privacy guard is active in this clone.
git config core.hooksPath .githooks
echo "✅ private state synced; pre-commit guard enabled."
echo "   Remember: after any prep session, commit & push inside ./private — that repo is the durable memory."
