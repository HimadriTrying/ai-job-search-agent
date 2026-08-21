#!/usr/bin/env bash
#
# check-cover-letter.sh — mechanical guard for a generated cover letter.
#
# Usage:
#   bash scripts/check-cover-letter.sh <letter.md> [options]
#
# Options:
#   --company NAME     Company the letter is addressed to. Inferred from the filename
#                      or parent directory when omitted.
#   --research PATH    Company research file. Auto-discovered when omitted (see below).
#   --facts PATH       Frozen facts file. Defaults to career_facts.yaml.
#   --no-research      Skip the research gate. Use only when the letter is deliberately
#                      not research-led; it removes the strongest check in this file.
#
# WHY THIS EXISTS
#
# A rule stated in a prompt gets followed most of the time. A rule that exits non-zero
# gets followed every time. The honesty gate (honesty/verify.py) already proves the letter
# does not fabricate. This script is the complementary question: is the letter any good,
# in the ways a script can actually determine?
#
# It cannot answer that fully, and it does not pretend to. Everything here is a floor.
# Passing every check below is NOT evidence the letter is good. In real use, letters that
# passed every mechanical check were still sent back with ten content faults by a reviewer
# subagent reading the same spec. Run the Reviewer. See docs/FAILURE-MODES.md.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

LETTER=""; COMPANY=""; RESEARCH=""; FACTS="career_facts.yaml"; DO_RESEARCH=1
while [ $# -gt 0 ]; do
  case "$1" in
    --company)     COMPANY="${2:-}"; shift 2 ;;
    --research)    RESEARCH="${2:-}"; shift 2 ;;
    --facts)       FACTS="${2:-}"; shift 2 ;;
    --no-research) DO_RESEARCH=0; shift ;;
    -h|--help)     sed -n '2,26p' "$0"; exit 0 ;;
    *)             LETTER="$1"; shift ;;
  esac
done

[ -n "$LETTER" ] || { echo "usage: check-cover-letter.sh <letter.md> [--company NAME]" >&2; exit 1; }
[ -f "$LETTER" ] || { echo "no such file: $LETTER" >&2; exit 1; }

# Infer the company from "<something>-<company>.md", "cover-<company>.md" or the parent dir.
if [ -z "$COMPANY" ]; then
  base="$(basename "$LETTER" .md)"
  COMPANY="$(printf '%s' "$base" | sed -E 's/.*[Cc]over[-_]?([Ll]etter)?[-_]//; s/[-_](letter|cover)$//')"
  [ "$COMPANY" = "$base" ] && COMPANY="$(basename "$(dirname "$LETTER")")"
fi

# Auto-discover the research file across the conventional locations.
if [ -z "$RESEARCH" ]; then
  for cand in \
    "data/research/$COMPANY.md" \
    "data/research/$COMPANY/company-research.md" \
    "private/processes/$COMPANY/company-research.md"; do
    [ -s "$cand" ] && { RESEARCH="$cand"; break; }
  done
fi

FAIL=0
ok()  { printf '  PASS %s\n' "$1"; }
bad() { printf '  FAIL %s\n' "$1"; FAIL=1; }
note(){ printf '       %s\n' "$1"; }

echo "Checking $LETTER  (company: $COMPANY)"

PROSE=$(python3 - "$LETTER" <<'PYEOF'
import re,sys
t=open(sys.argv[1]).read()
t=re.sub(r'```.*?```','',t,flags=re.S)
t=re.sub(r'<!--.*?-->','',t,flags=re.S)
sys.stdout.write('\n'.join(l for l in t.split('\n') if not l.lstrip().startswith('#')))
PYEOF
)

# 1. Dashes used as punctuation, in every form.
#    Ban the behaviour, not the one character you happened to catch: a rule that says
#    "no em dashes" is satisfied by an en dash or a spaced hyphen, and the same defect
#    comes straight back. Hyphens INSIDE words are legitimate and are not flagged.
D=0
grep -q '—' <<<"$PROSE" && { bad "em dash in prose"; D=1; }
grep -q '–' <<<"$PROSE" && { bad "en dash in prose"; D=1; }
grep -qE '[[:alnum:],]) - |[[:alnum:]] - [[:alnum:]]' <<<"$PROSE" \
  && { bad "spaced hyphen used as a dash (use a comma, semicolon or full stop)"; D=1; }
[ "$D" = "0" ] && ok "no dashes used as punctuation (compound hyphens are fine)"

# 2. Length. Longer is not more convincing, it is less read.
W=$(wc -w <<<"$PROSE")
if   [ "$W" -lt 200 ]; then bad "$W words, under the 200 word floor"
elif [ "$W" -gt 280 ]; then bad "$W words, over the 280 word cap (cut, do not shrink the argument)"
else ok "$W words (band 200-280)"; fi

# 3. Registers that read as a brochure rather than a person.
H=0
for p in "world-class" "best-in-class" "cutting-edge" "state-of-the-art" "passionate" \
         "thrilled" "delighted" "perfect fit" "dream role" "proven track record" \
         "results-driven" "results driven" "highly motivated" "leverage" "synergy" \
         "spearhead" "seamless" "game-changer" "deeply excited" "truly excited" \
         "incredibly excited" "wealth of experience" "hit the ground running"; do
  grep -qi -- "$p" <<<"$PROSE" && { bad "selling register: \"$p\""; H=$((H+1)); }
done
for p in "heard good things" "excited about the opportunity" "excited to apply" \
         "I am writing to apply" "I am writing to express" "would like to express my interest" \
         "great admiration" "long been an admirer" "big fan of"; do
  grep -qi -- "$p" <<<"$PROSE" && { bad "generic enthusiasm: \"$p\" (needs a researched line)"; H=$((H+1)); }
done
# Self-aware pre-emption. State the reasoning directly instead of flagging that you are
# about to state it.
for p in "you might be wondering" "you may be wondering" "while I don't have" \
         "while I do not have" "although I lack" "I know this may sound" \
         "I realise this is unusual" "I realize this is unusual"; do
  grep -qi -- "$p" <<<"$PROSE" && { bad "self-aware pre-emption: \"$p\" (say the thing)"; H=$((H+1)); }
done
# Explaining the company to the company. They know what they do; the paragraph spent
# telling them is a paragraph not spent on the candidate.
for p in "is a leading" "is one of the leading" "founded in" "you are building" \
         "you're building" "as a company that" "the company behind" "your mission is" \
         "specialises in" "specializes in" "you have built" "you've built" \
         "has grown into" "is known for"; do
  grep -qi -- "$p" <<<"$PROSE" && { bad "explains the company to itself: \"$p\""; H=$((H+1)); }
done
if [ -n "$COMPANY" ] && grep -qiE "\b$COMPANY (is|was|has been) an? " <<<"$PROSE"; then
  bad "explains the company to itself: \"$COMPANY is a ...\""; H=$((H+1))
fi
[ "$H" = "0" ] && ok "no banned registers"

# 4. Placeholders must never reach a human.
grep -qE '\{\{[A-Za-z_]+\}\}|\[COMPANY\]|\[ROLE\]|\[NAME\]|XXX|TODO|TK' <<<"$PROSE" \
  && bad "unfilled placeholder in the letter" || ok "no placeholders"

# 5. The company name. Sending Company A's letter to Company B is the single most
#    catastrophic and most common cover letter failure, and it is trivially checkable.
if [ -n "$COMPANY" ] && grep -qi -w -- "$COMPANY" <<<"$PROSE"; then
  ok "addresses $COMPANY by name"
else
  bad "the letter never names $COMPANY"
fi
OTHERS=0
for d in data/research/*/ private/processes/*/; do
  [ -d "$d" ] || continue
  o="$(basename "$d")"
  [ "$o" = "$COMPANY" ] && continue
  grep -qi -w -- "$o" <<<"$PROSE" && { bad "WRONG COMPANY: \"$o\" appears in a letter to $COMPANY"; OTHERS=1; }
done
[ "$OTHERS" = "0" ] && ok "no other researched company named"

# 6. Numeric honesty gate. Cheap, deterministic, and complementary to honesty/verify.py:
#    every figure in the letter must literally appear in the frozen facts file. Catches
#    the common failure where a draft rounds a number up because it reads better.
if [ -f "$FACTS" ]; then
  python3 - "$LETTER" "$FACTS" <<'PYEOF'
import re,sys
t=open(sys.argv[1]).read()
t=re.sub(r'```.*?```','',t,flags=re.S); t=re.sub(r'<!--.*?-->','',t,flags=re.S)
t='\n'.join(l for l in t.split('\n') if not l.lstrip().startswith('#'))
facts=open(sys.argv[2]).read()
nums=set(re.findall(r'\d+(?:\.\d+)?',t)); fn=set(re.findall(r'\d+(?:\.\d+)?',facts))
isyear=lambda n: re.fullmatch(r'(19|20)\d\d',n) is not None
bad=sorted(n for n in nums if not isyear(n) and n not in fn)
if bad:
    print(f"  FAIL figures not in {sys.argv[2]}: {', '.join(bad)}")
    print("       Add it to the frozen facts first, or take it out of the letter.")
    sys.exit(1)
kept=sorted(n for n in nums if not isyear(n))
print(f"  PASS {len(kept)} figure(s) traced to {sys.argv[2]}" + (f": {', '.join(kept)}" if kept else " (none used)"))
PYEOF
  [ $? -ne 0 ] && FAIL=1
else
  printf '  SKIP no %s, numeric honesty gate not run\n' "$FACTS"
fi

# 7. The research gate. The strongest check here, because it fails at the cause instead
#    of the symptom: a letter cannot be "researched" if nobody ran the research. In real
#    use a letter passed every other check on a company whose research had never been
#    done, which made the "reference something specific about them" rule decoration.
if [ "$DO_RESEARCH" = "0" ]; then
  printf '  SKIP research gate disabled with --no-research\n'
elif [ -n "$RESEARCH" ] && [ -s "$RESEARCH" ]; then
  ok "company research exists: $RESEARCH"
else
  bad "NO RESEARCH for $COMPANY"
  note "run the company-research skill first. Looked for:"
  note "  data/research/$COMPANY.md"
  note "  data/research/$COMPANY/company-research.md"
  note "  private/processes/$COMPANY/company-research.md"
  note "the letter is not ready to draft without it."
fi

# 8-12. Story shape, the callback, grounding, and readability.
python3 - "$LETTER" "${RESEARCH:-}" "$COMPANY" "$DO_RESEARCH" <<'PYEOF'
import re,sys

STOP=set("""a about above after again against all also am an and any are as at be because
been before being below between both but by can could did do does doing down during each few
for from further had has have having he her here hers him his how i if in into is it its just
let me more most my no nor not of off on once only or other ought our out over own same she
should so some such than that the their them then there these they this those through to too
under until up very was we were what when where which while who whom why with would you your
already always another because before better build building built come every first give going
great know like made make many much need never really right since still take thing think time
want well were work working year years role team across without whatever toward towards""".split())

def clean(t):
    t=re.sub(r'```.*?```','',t,flags=re.S); t=re.sub(r'<!--.*?-->','',t,flags=re.S)
    return '\n'.join(l for l in t.split('\n') if not l.lstrip().startswith('#'))

def toks(t,n):
    return {w for w in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", t.lower()) if len(w)>=n and w not in STOP}

letter, research, company, do_research = sys.argv[1], sys.argv[2], sys.argv[3].lower(), sys.argv[4]=="1"
body=clean(open(letter).read())

paras=[p.strip() for p in body.split('\n\n') if p.strip()]
greet=lambda p: re.match(r'^(dear|hi|hello|to whom)\b',p,re.I) is not None
def signoff(p):
    p=p.strip()
    if len(p.split())>6: return False
    if re.search(r'\b(regards|sincerely|best|thanks|thank you|yours)\b',p,re.I): return True
    # A bare name line, e.g. "Jane Doe" or "Jane Doe,"
    return re.fullmatch(r"[A-Z][a-z'’-]+(\s+[A-Z][a-z'’-]+)*[,.]?",p) is not None
beats=[p for p in paras if not greet(p) and not signoff(p)]
fails=[]

# 8. Four beats: observation, flagship proof, turn, callback. Load-bearing, because the
#    callback needs a beat 1 to set up and a beat 4 to pay off.
if len(beats)==4: print("  PASS 4 beats (observation, flagship, turn, callback)")
else: fails.append(f"{len(beats)} beats, the shape is 4 (observation, flagship, turn, callback)")

# 9. The callback. A closing beat that shares no vocabulary with its own opening will not
#    read as a callback in 250 words, and the letter reverts to four standalone blocks.
if len(beats)>=2:
    shared=sorted(toks(beats[0],5) & toks(beats[-1],5))
    if shared: print(f"  PASS closer calls back to the opening: {', '.join(shared[:4])}")
    else: fails.append("NO CALLBACK: the closer shares no distinctive term with the opening. "
                       "The last beat must return to the observation the first beat set up.")

# 10. Grounded in the research. Requiring the file to exist catches the skipped step;
#     requiring overlap catches the case where the file exists and the model wrote the
#     letter from its own memory of the company anyway.
if do_research and research:
    try: rtext=open(research).read()
    except OSError: rtext=""
    if rtext.strip():
        shared=sorted((toks(body,6)-{company}) & toks(rtext,6))
        if len(shared)>=2: print(f"  PASS grounded in research: {', '.join(shared[:6])}")
        else: fails.append("NOT GROUNDED: the letter shares fewer than 2 distinctive terms with "
                           "the research file, so its 'researched' point is not traceable to any "
                           "research. Name the specific thing the sweep actually found.")

# 11. Sayable in one breath. A letter is read in a voice; a sentence that needs a second
#     run at it has lost the reader.
sents=[s.strip() for s in re.split(r'(?<=[.!?])\s+',' '.join(beats)) if s.strip()]
long=[s for s in sents if len(s.split())>35]
if long:
    for s in long: fails.append(f"sentence runs {len(s.split())} words (cap 35): \"{s[:70]}...\"")
else:
    print(f"  PASS {len(sents)} sentences, longest {max((len(s.split()) for s in sents),default=0)} words (cap 35)")

# 12. The modular-blocks tell. Beats that each open with "I" are four standalone
#     paragraphs wearing a story's clothes.
i=sum(1 for p in beats if re.match(r"^I[ '’]",p))
if i>=3: fails.append(f"{i} of {len(beats)} beats open with \"I\": these are modules, not beats. "
                      "Each beat has to carry the one before it.")
else: print(f"  PASS beats do not all open the same way ({i} open with \"I\")")

for f in fails: print(f"  FAIL {f}")
sys.exit(1 if fails else 0)
PYEOF
[ $? -ne 0 ] && FAIL=1

# 13. The rules the user taught Lucy themselves (the correction loop).
#     Everything above this line is the house spec: universal, shipped, the same for
#     everyone. This step is the other half — the rules this particular user asked for after
#     rejecting a draft, stored in profile/learned-rules.yaml. Without it a correction fixes
#     one letter and dies with the session, and the same correction arrives again next week.
#     A store that does not exist yet is not a failure: a new user has taught it nothing.
echo "-- learned rules (yours, from profile/learned-rules.yaml)"
if command -v python3 >/dev/null 2>&1 && [ -f "scripts/learned_rules.py" ]; then
  python3 "scripts/learned_rules.py" --store "profile/learned-rules.yaml" \
      check "$LETTER" --scope letter | sed 's/^/  /'
  [ "${PIPESTATUS[0]}" -ne 0 ] && FAIL=1
else
  echo "  SKIP python3 or scripts/learned_rules.py unavailable"
fi

echo
if [ "$FAIL" = "0" ]; then
  echo "Mechanical checks passed. This is a floor, not a verdict: now run the Reviewer"
  echo "subagent against the spec in profile/06-cover-letter-notes.md before anyone sends it."
  exit 0
else
  echo "CHECKS FAILED — do not send this letter."
  exit 1
fi
