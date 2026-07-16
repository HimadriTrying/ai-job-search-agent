#!/usr/bin/env bash
# Claude Code PostToolUse hook — the DESIGN gate, enforced by machinery.
#
# Sibling of honesty-hook.sh. Fires after every Write/Edit; if the file is an
# HTML deliverable under applications/, it checks the design conventions that
# have been silently missed before (each check below exists because a real
# deliverable shipped without it):
#
#   1. Cover-letter letterheads must carry the target company's logo
#      (aGYM letter shipped without one, 2026-07-16).
#   2. CSS grids must not use paired percentage columns — "30% 70%" + gap
#      overflows A4 in headless Chrome and clips the right edge (all three
#      CV PDFs shipped clipped, caught 2026-07-16). Use fr units.
#   3. Print scaffolding must exist: @page rule + .noprint banner.
#
# On failure the findings go back to Claude on stderr (exit 2) so the file is
# fixed in the same turn. Safe on forks: silent if the file isn't a deliverable.
set -u

payload=$(cat)
file=$(printf '%s' "$payload" | python3 -c \
  "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" \
  2>/dev/null) || exit 0

[ -z "$file" ] && exit 0

case "$file" in
  */applications/*.html) ;;
  *) exit 0 ;;
esac

[ -f "$file" ] || exit 0

fails=""

# 1. Letterhead logo on cover letters.
case "$(basename "$file")" in
  *CoverLetter*|*cover-letter*|*coverletter*)
    if ! grep -q 'class="logo"' "$file"; then
      fails="${fails}  ✗ No letterhead logo (class=\"logo\") — every cover letter carries the company's real logo (profile/03).\n"
    fi
    ;;
esac

# 2. Percentage grid columns (A4 clipping bug in headless Chrome).
if grep -qE 'grid-template-columns:[^;]*[0-9]+%[[:space:]]+[0-9]+%' "$file"; then
  fails="${fails}  ✗ grid-template-columns uses paired % widths — overflows A4 with gap and clips the right edge. Use fr units (e.g. 30fr 70fr).\n"
fi

# 3. Print scaffolding.
if ! grep -q '@page' "$file"; then
  fails="${fails}  ✗ Missing @page rule (A4 size + margins for print).\n"
fi
if ! grep -q 'noprint' "$file"; then
  fails="${fails}  ✗ Missing .noprint save-as-PDF banner.\n"
fi

[ -z "$fails" ] && exit 0

{
  echo "DESIGN GATE (automatic hook) failed for: $file"
  echo ""
  printf '%b' "$fails"
  echo ""
  echo "These are the deliverable conventions from profile/03-writing-style.md."
  echo "Fix the HTML before presenting; re-render and visually verify the PDF after."
} >&2
exit 2
