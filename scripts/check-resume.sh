#!/bin/bash
#
# check-resume.sh — mechanical guard for a generated CV.
#
# Usage:
#   bash scripts/check-resume.sh <resume.html> [--facts PATH] [--no-render]
#   bash scripts/check-resume.sh --all          # sweep every CV under applications/
#
# WHY THIS EXISTS
#
# A rule stated in a prompt gets followed most of the time. A rule that exits non-zero gets
# followed every time. The honesty gate proves a CV does not lie; this proves it is built the
# way profile/08-cv-notes.md says it should be.
#
# WHY --all EXISTS
#
# A rule fixed on the document that triggered it never reached the others: in real use one CV
# sat failing twenty of twenty-one checks for four days, because the checks only ever ran on
# whatever was being worked on. Run the sweep whenever a shared file changes.
#
# WHAT IT CANNOT DO
#
# Everything here is a floor. The rules that actually cost rounds are the ones no script can
# see: a bullet that states a duty rather than an outcome, three achievements at equal weight,
# a claim true only within a scope it does not name. Passing every check below is NOT evidence
# the CV is good. Run the Reviewer. See docs/FAILURE-MODES.md.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

FACTS="career_facts.yaml"; DO_RENDER=1; TARGETS=(); SWEEP=0
while [ $# -gt 0 ]; do
  case "$1" in
    --all)         SWEEP=1; shift ;;
    --facts)       FACTS="${2:-}"; shift 2 ;;
    --no-render)   DO_RENDER=0; shift ;;
    -h|--help)     sed -n '2,25p' "$0"; exit 0 ;;
    *)             TARGETS+=("$1"); shift ;;
  esac
done

if [ "$SWEEP" = "1" ]; then
  while IFS= read -r f; do TARGETS+=("$f"); done < <(
    find applications data/drafts drafts -type f \
         \( -iname '*resume*.html' -o -iname '*cv*.html' \) 2>/dev/null | sort)
  if [ "${#TARGETS[@]}" -eq 0 ]; then
    echo "sweep: no CVs found under applications/, data/drafts/ or drafts/"
    exit 0
  fi
fi

[ "${#TARGETS[@]}" -gt 0 ] || { echo "usage: check-resume.sh <resume.html> | --all" >&2; exit 1; }

# ---------------------------------------------------------------- design system, checked once
#
# The type hierarchy is a property of the stylesheet, not of any one CV, so it is checked once
# per run rather than per document. A section heading must be strictly larger than the role
# heading beneath it, which must be strictly larger than body text. When a subheading matches
# its heading the page reads as one flat block and a ten-second skim finds nothing to catch on.
CSS="templates/resume.css"
DESIGN_FAIL=0
if [ -f "$CSS" ]; then
  echo "-- design system ($CSS)"
  if ! python3 - "$CSS" <<'PY'
import re, sys
css = open(sys.argv[1], encoding="utf-8").read()
def pt(var):
    m = re.search(rf"--{var}:\s*([0-9.]+)pt", css)
    return float(m.group(1)) if m else None
name, section, role, body = pt("size-name"), pt("size-section"), pt("size-role"), pt("size-body")
missing = [n for n, v in (("size-name", name), ("size-section", section),
                          ("size-role", role), ("size-body", body)) if v is None]
if missing:
    print(f"  FAIL stylesheet does not define {', '.join(missing)} in pt")
    sys.exit(1)
bad = []
if not name > section: bad.append(f"name {name}pt must exceed section {section}pt")
if not section > role: bad.append(f"section {section}pt must exceed role {role}pt")
if not role > body:    bad.append(f"role {role}pt must exceed body {body}pt")
if bad:
    for b in bad: print(f"  FAIL type hierarchy: {b}")
    sys.exit(1)
print(f"  PASS type hierarchy {name} > {section} > {role} > {body} pt")
PY
  then DESIGN_FAIL=1; fi
else
  echo "  SKIP $CSS not found"
fi

# ---------------------------------------------------------------- per resume
check_one() {
  local DOC="$1" FAIL=0
  echo
  echo "Checking $DOC"
  [ -f "$DOC" ] || { echo "  FAIL no such file"; return 1; }

  python3 - "$DOC" "$CSS" <<'PY' || FAIL=1
import re, sys, os
doc_path, css_path = sys.argv[1], sys.argv[2]
html = open(doc_path, encoding="utf-8", errors="replace").read()
fails, passes = [], []

# 1. The design system is LINKED, not inlined. A document that carries its own copy of the
#    sizes and colours is one that can drift from every other document, which is the whole
#    failure the stylesheet exists to remove.
styles = re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I)
inlined = [s for s in styles
           if re.search(r"(font-size|--size-|color\s*:|margin|padding)", s, re.I)]
if inlined:
    fails.append("a <style> block re-implements the design system. Link "
                 f"{os.path.basename(css_path)} and change it there instead")
elif re.search(r'<link[^>]+resume\.css', html, re.I):
    passes.append("design system is linked, not inlined")
else:
    fails.append(f"does not link {os.path.basename(css_path)}: layout will be improvised")

# 2. Nothing clips its own overflow. `overflow: hidden` on a fixed-height page silently
#    deletes the last bullets and the page count still reports the number you wanted, so the
#    document lies about being finished. Let it spill and look wrong instead.
clip = re.search(r"overflow\s*:\s*(hidden|clip)", html, re.I)
if clip:
    fails.append(f"'{clip.group(0)}' in the document: a clipped page hides content it cannot "
                 "fit and still reports the page count you wanted. Use overflow: visible")
else:
    passes.append("no clipped overflow: the page count can tell the truth")

# Prose only, for the text checks below: strip tags, comments, scripts and styles.
text = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
text = re.sub(r"<[^>]+>", " ", text)
text = re.sub(r"\s+", " ", text)

# 3. Quantities as numerals. A skim is looking for digits; spelled-out numbers read as prose
#    and vanish. "one" is excluded: it is idiomatic far more often than it is a count.
WORDS = ("two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|"
         "forty|fifty|hundred|thousand|million|billion")
UNITS = ("years?|months?|weeks?|days?|hours?|quarters?|sprints?|people|persons?|engineers?|"
         "designers?|teams?|squads?|markets?|regions?|countries|companies|clients?|customers?|"
         "products?|platforms?|integrations?|percent|million|billion|users?|accounts?|reports?")
spelled = re.findall(rf"\b({WORDS})[- ]({UNITS})\b", text, re.I)
if spelled:
    shown = ", ".join(f"{a} {b}" for a, b in spelled[:4])
    fails.append(f"spelled-out quantity: {shown}. Write numerals and symbols (30%, not "
                 "thirty percent)")
else:
    passes.append("quantities use numerals")

# 4. A change keeps both sides. "to 30 days" with no baseline is a number with no story, and
#    the baseline is what gets dropped when a line is trimmed for space. Advisory, not fatal:
#    plenty of legitimate lines say "to" without describing a change.
half = []
for m in re.finditer(r"\b(?:reduc\w+|cut|drop\w*|improv\w+|grew|grow\w*|increas\w+|rais\w+)"
                     r"[^.]{0,60}?\bto\s+([0-9][0-9.,]*\s*[%a-zA-Z]*)", text, re.I):
    window = text[max(0, m.start() - 90): m.end()]
    if not re.search(r"\bfrom\b", window, re.I):
        half.append(m.group(0).strip()[:60])
if half:
    print("  NOTE before/after claim with no baseline (review, not a failure):")
    for h in half[:3]:
        print(f"       \"{h}\" - say what it was before, or the number carries no story")

# 5. Placeholders must never reach a human.
ph = re.findall(r"(lorem ipsum|TODO|TBD|FIXME|XXX+|\[[A-Za-z ]{3,20}\]|Your Name|you@example\.com)",
                text)
if ph:
    fails.append(f"placeholder text still present: {', '.join(sorted(set(ph))[:4])}")
else:
    passes.append("no placeholders")

# 6. A contact block exists. A CV with no way to reply is a surprisingly survivable bug.
if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text) or re.search(r"linkedin\.com/in/", html, re.I):
    passes.append("contact details present")
else:
    fails.append("no email or LinkedIn found: the reader cannot reply")

# 7. Links are real links. A printed CV is read on screen far more often than on paper.
if re.search(r'href="https?://', html, re.I):
    passes.append("carries at least one real hyperlink")
else:
    print("  NOTE no hyperlinks found. A portfolio or LinkedIn link is usually worth one.")

for p in passes: print(f"  PASS {p}")
for f in fails:  print(f"  FAIL {f}")
sys.exit(1 if fails else 0)
PY

  # 8. The user's own learned rules (the correction loop).
  if [ -f scripts/learned_rules.py ] && command -v python3 >/dev/null 2>&1; then
    python3 scripts/learned_rules.py --store profile/learned-rules.yaml \
        check "$DOC" --scope cv | sed 's/^/  /'
    [ "${PIPESTATUS[0]}" -ne 0 ] && FAIL=1
  fi

  # 9. Page count, when a renderer exists. Checking the RENDERED artefact rather than the
  #    source matters: several real faults were invisible in the HTML and only showed up in
  #    the PDF. A missing renderer is a skip, never a silent pass.
  if [ "$DO_RENDER" = "1" ]; then
    local CHROME=""
    for c in chromium chromium-browser google-chrome "$PLAYWRIGHT_BROWSERS_PATH/chromium"; do
      command -v "$c" >/dev/null 2>&1 && { CHROME="$c"; break; }
    done
    if [ -n "$CHROME" ]; then
      local PDF; PDF="$(mktemp -t resume-XXXXXX.pdf)"
      if "$CHROME" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
           --print-to-pdf="$PDF" "$DOC" >/dev/null 2>&1 && [ -s "$PDF" ]; then
        local PAGES
        PAGES="$(python3 -c "
import re,sys
d=open(sys.argv[1],'rb').read()
print(max(len(re.findall(rb'/Type\s*/Page[^s]', d)), 1))" "$PDF" 2>/dev/null || echo 0)"
        if [ "$PAGES" -gt 2 ] 2>/dev/null; then
          echo "  FAIL renders to $PAGES pages (cap 2). Cut by relevance, per rule 7"
          FAIL=1
        else
          echo "  PASS renders to $PAGES page(s)"
        fi
      else
        echo "  SKIP could not render with $CHROME"
      fi
      rm -f "$PDF"
    else
      echo "  SKIP no Chromium found: page count unverified (pass --no-render to silence)"
    fi
  fi

  # 10. The honesty gate, when the frozen facts exist.
  if [ -f "$FACTS" ] && [ -f honesty/verify.py ]; then
    if python3 honesty/verify.py "$DOC" --facts "$FACTS" >/dev/null 2>&1; then
      echo "  PASS honesty gate"
    else
      echo "  FAIL honesty gate: run 'python honesty/verify.py $DOC' for detail"
      FAIL=1
    fi
  else
    echo "  SKIP honesty gate ($FACTS not found: run setup)"
  fi

  return $FAIL
}

RC=0
for doc in "${TARGETS[@]}"; do
  check_one "$doc" || RC=1
done
[ "$DESIGN_FAIL" = "1" ] && RC=1

echo
if [ "$RC" = "0" ]; then
  echo "Mechanical checks passed. This is a floor, not a verdict: a duty dressed as an"
  echo "outcome, three achievements at equal weight, and a claim that does not name its"
  echo "scope all pass everything above. Run the Reviewer against profile/08-cv-notes.md."
  exit 0
fi
echo "CHECKS FAILED — this CV is not finished."
exit 1
