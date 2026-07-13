# Job Evaluation Rubric

The scoring rubric that decides *yes / worth-a-look / no* for you specifically. Two design
rules, both borrowed from the reference systems and both important:

1. **Mostly penalties, not bonuses.** A rubric that says yes to everything is not a filter.
   The value is in aggressive subtraction.
2. **Filters drop, they don't downrank.** Out-of-band roles are removed *before* any
   expensive tailoring, not scored low and kept. Cheaper and cleaner.

---

## Hard drops (remove before scoring — never spend an LLM call on these)

### Seniority floor — INVERTED for this candidate ⚠
The usual job filter is a ceiling that drops roles *above* a junior candidate. Here it is
the opposite — a floor. Your target is Senior / Lead / Staff / Group PM, so the knob is a **`min_seniority`
that drops everything BELOW Senior.**

- DROP: Associate PM, Junior PM, APM, PM I, "early career", most generic "Product Manager"
  with < Senior scope.
- KEEP: Senior PM, Lead PM, Staff PM, Group PM, Principal PM, Head of Product (small org),
  and AI-product-builder roles at those levels.
- Title→level mapping lives in `seniority.py` — a floor that drops everything below Senior.

### Experience ceiling — fire only on hard-cued minimums
Drop only when the minimum is *hard-cued*: "8 years **required** / **must** / **minimum** /
**at least**". Do **not** drop on soft phrasing: "8+ years **preferred**", "or equivalent",
or a bare number. This avoids over-filtering on language that isn't actually a gate.

### Other hard drops
- Wrong location / no remote when you need remote
- No work authorization match
- Industry on your personal exclusion list (define below)

---

## Penalties (subtract; this is where the rubric earns its keep)

| Condition | Penalty | Why |
|---|---|---|
| Requires 5+ yrs in a domain you lack | −−− | Long shots waste funnel capacity |
| Unfamiliar core platform/tech stack | −− | Ramp cost, weaker interview story |
| Vague JD / boilerplate, no real scope | −− | Signals disorganised hiring or low altitude |
| No mention of strategy/direction at a "senior" title | −− | Mislabelled IC role in disguise |
| Big brand, thousands of applicants, no warm path | − | Low conversion without a referral |
| Comp band below your floor (if disclosed) | −− | Define floor below |
| Culture red flags (churn language, "wear many hats" at senior level) | − | |

## Bonuses (add sparingly — keep the rubric net-negative)

| Condition | Bonus | Why |
|---|---|---|
| AI-forward team / genuine AI-builder scope | ++ | Directly on-target |
| Explicit Staff/Group altitude (vision, cross-team influence) | ++ | Where you want to be |
| A warm intro path exists (from `network-mapper`) | ++ | Materially changes conversion |
| Stack / domain you can tell a strong story about | + | Stronger tailoring + interview |

---

## Your knobs — fill these in

```yaml
min_seniority: "Senior"          # drop below this
hard_experience_gate_years: 8    # only drops on hard-cued minimums
required_locations: []           # e.g. ["Berlin", "Remote-EU"]
comp_floor: null                 # e.g. 95000 (currency below)
comp_currency: "EUR"
excluded_industries: []          # e.g. ["gambling", "defense"]
must_have_keywords: []           # a role missing ALL of these is suspect
nice_to_have_keywords: []        # AI, LLM, platform, 0-to-1, marketplace...
```

## Buckets
After scoring, sort every surviving role into three buckets:
**apply first / worth a look / skipped** — with a one-line reason each.
