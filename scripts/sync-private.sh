#!/usr/bin/env bash
# Sync your PRIVATE data repo into this clone and link the files the skills expect.
# The private repo holds everything .gitignore keeps out of this public one: the real
# career_facts.yaml, profile/*.md, tracker, connections, and generated applications.
#
# Usage:
#   scripts/sync-private.sh <git-url-of-your-private-repo>   # first run: clones to private/
#   scripts/sync-private.sh                                  # later runs: pulls private/
#
# Idempotent; safe to run at the start of every session (local or remote). In a remote
# session, add the private repo to the session first so the clone is authorized.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d private/.git ]; then
  if [ $# -lt 1 ]; then
    echo "private/ not present yet. First run needs your private repo's git URL:" >&2
    echo "  scripts/sync-private.sh <git-url-of-your-private-repo>" >&2
    exit 1
  fi
  git clone "$1" private
else
  git -C private pull --ff-only
fi

# Link real files over the *.example defaults. ln -sf is idempotent; only links what
# actually exists in the private repo, so a partially-migrated repo still works.
link() { # link <path-inside-private/> <path-in-this-repo>
  if [ -e "private/$1" ]; then
    mkdir -p "$(dirname "$2")"
    ln -sf "$(pwd)/private/$1" "$2"
  fi
}

link career_facts.yaml career_facts.yaml
link data/tracker.csv data/tracker.csv
for f in private/profile/[0-9][0-9]-*.md private/data/connections/*.csv private/data/jd/*.md; do
  [ -e "$f" ] || continue
  rel="${f#private/}"
  link "$rel" "$rel"
done
# Generated application docs live in the private repo; expose them at applications/.
if [ -d private/applications ]; then
  ln -sfn "$(pwd)/private/applications" applications
fi

echo "Private data synced from private/ (linked whatever exists there: facts, profile, tracker, jd, connections, applications)."
[ -e career_facts.yaml ] || echo "NOTE: career_facts.yaml still missing — the honesty gate cannot run until it exists." >&2
