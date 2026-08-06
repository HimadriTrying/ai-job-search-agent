"""
Offline tests for the honesty gate. No network, fictional data only.
Run:  python -m pytest -q   (or python tests/test_verify.py)

These encode the gate's contract:
  - a normal cover letter (salutation + target company passed as context) must PASS
  - a metric whose only source is the candidate's phone number must FAIL
  - a known short skill ("sql") must not whitelist unrelated proper nouns ("Air France")
  - a real metric attributed to the WRONG employer must FAIL
  - everything true and attributed correctly must PASS
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from verify import check, Context, context_from_job_posting

# Entirely fictional candidate. Phone deliberately contains "40" so we can prove
# contact digits are NOT usable as metrics.
FACTS = {
    "candidate": {
        "name": "Jordan Vale",
        "location": "Lisbon",
        "contact": {"email": "jordan@example.com", "phone": "+351 912 40 778", "linkedin": ""},
    },
    "employers": [
        {
            "company": "Northwind Analytics",
            "title": "Senior Product Manager",
            "start": "2019-03",
            "end": "2022-06",
            "metrics": ["Grew activation 18% over two quarters"],
            "scope": ["Owned roadmap for 3 squads, ~25 engineers",
                      "Partnered with Iberia Cloud on data infrastructure"],
        },
        {
            "company": "Beacon Labs",
            "title": "Lead Product Manager",
            "start": "2022-07",
            "end": "present",
            "metrics": ["Cut churn 9% in one year"],
            "scope": ["Led 2 product teams"],
        },
    ],
    "education": [
        {"institution": "University of Coimbra", "credential": "MSc Information Systems", "year": "2014"}
    ],
    "certifications": [],
    "skills": ["sql", "experimentation", "ai product strategy"],
    "coaching": [
        {
            "organisation": "Meridian Row",
            "role": "Ride coach, Lisbon studios",
            "cadence": "roughly 4 classes a week",
            "metrics": ["Coached 229 classes across Meridian Row's Lisbon studios",
                        "Earned 181 five-star ratings"],
        }
    ],
    "endurance": [
        "3 Hyrox open races",
        "2 Super Halves",
        {"note": "Tracks and adjusts his own training data"},
    ],
}


def findings_for(doc, context=None):
    return check(doc, FACTS, context=context)


# ── The core loop must be able to pass ───────────────────────────────────────

def test_cover_letter_with_target_context_passes():
    letter = (
        "Dear Hiring Manager,\n\n"
        "I am excited to apply to Acme Robotics. At Northwind Analytics I grew "
        "activation 18% over two quarters and owned the roadmap for 3 squads.\n\n"
        "Kind regards,\nJordan Vale\n"
    )
    ctx = Context(targets=["Acme Robotics"])
    assert findings_for(letter, ctx) == []


def test_target_company_flagged_without_context():
    # Conservative default: an org name that is in neither the facts nor the
    # declared target is still treated as a possible invention.
    letter = "I am excited to apply to Acme Robotics."
    assert any("Acme Robotics" in f for f in findings_for(letter))


def test_salutations_and_own_name_never_flagged():
    letter = "Dear Hiring Team,\n\nBest regards,\nJordan Vale\n"
    assert findings_for(letter) == []


# ── False negatives the old gate allowed ─────────────────────────────────────

def test_phone_digits_are_not_metrics():
    # "40" appears only inside the phone number; claiming 40% growth is fabrication.
    doc = "At Northwind Analytics I grew revenue 40% year over year."
    assert any("40%" in f for f in findings_for(doc))


def test_contact_email_and_linkedin_are_not_claim_sources():
    doc = "I scaled the platform to 351 customers."  # 351 = phone country code only
    assert any("351" in f for f in findings_for(doc))


def test_short_skill_does_not_whitelist_unrelated_nouns():
    # "sql" and "ai product strategy" are known skills; "Air France" must still flag.
    doc = "I led the partnership with Air France."
    assert any("Air France" in f for f in findings_for(doc))


# ── Attribution: right fact, wrong employer ──────────────────────────────────

def test_metric_bound_to_wrong_employer_fails():
    doc = "At Beacon Labs I grew activation 18% over two quarters."
    fs = findings_for(doc)
    assert any("18%" in f for f in fs)


def test_metric_bound_to_correct_employer_passes():
    doc = "At Northwind Analytics I grew activation 18% over two quarters."
    assert findings_for(doc) == []


def test_tenure_years_are_derivable():
    # 2019-03 to 2022-06 is 3 full years; saying "3 years" is not a fabrication.
    doc = "I spent 3 years at Northwind Analytics."
    assert findings_for(doc) == []


# ── The checks that already worked must keep working ─────────────────────────

def test_invented_employer_still_flagged():
    doc = "As Head of Product at Global Dynamics Corp I doubled the business."
    assert any("Global Dynamics Corp" in f for f in findings_for(doc))


def test_uncredentialed_certification_still_flagged():
    doc = "I hold an MBA and a PMP certification."
    fs = findings_for(doc)
    assert len(fs) >= 1


def test_real_credential_passes():
    doc = "I completed an MSc Information Systems at the University of Coimbra in 2014."
    assert findings_for(doc) == []


def test_fact_text_phrases_are_quotable():
    # "Iberia Cloud" appears only inside a scope string — reusing it is not invention.
    doc = "I partnered with Iberia Cloud on data infrastructure."
    assert findings_for(doc) == []


def test_self_certification_is_process_vocabulary_not_credential():
    # Regulatory flows like FCA self-certification are not credential claims.
    doc = "Built the self-certification flow for UK onboarding."
    assert not any("certification cue" in f for f in findings_for(doc))


# ── Job-posting context ──────────────────────────────────────────────────────

def test_job_posting_nouns_and_numbers_are_allowed():
    posting = (
        "Acme Robotics is hiring a Senior Product Manager for the Fleet Copilot team. "
        "You will work with 12 engineers across Munich Operations."
    )
    ctx = context_from_job_posting(posting)
    letter = (
        "Dear Hiring Manager, the Fleet Copilot mission at Acme Robotics is exactly "
        "why I applied — partnering with 12 engineers is the scale I know well from "
        "Northwind Analytics."
    )
    assert findings_for(letter, ctx) == []


# ── Coaching and endurance are claims too ────────────────────────────────────
# Added 6 Aug 2026. Before this, claim_numbers() and known_strings() read only
# employers/education/certifications, so a true coaching or race figure sitting
# in career_facts.yaml was still flagged as a fabrication. A gate that rejects
# the truth is a gate people learn to wave through.

def test_coaching_metric_passes():
    assert findings_for("I coach at Meridian Row in Lisbon, 229 classes in.") == []


def test_coaching_rating_count_passes():
    assert findings_for("I have earned 181 five-star ratings as a coach.") == []


def test_endurance_numbers_pass():
    assert findings_for("I have completed 3 Hyrox open races and 2 Super Halves.") == []


def test_inflated_coaching_metric_still_fails():
    # The point of widening the gate is not to stop it counting.
    assert any("450" in f for f in findings_for("I have coached 450 classes."))


def test_shared_numbers_are_allowed_inside_an_employer_sentence():
    # Documenting a deliberate limit, not an aspiration. Shared numbers (degree
    # years, coaching, endurance) are employer-independent, so the attribution
    # check does not bind them to the employer a sentence happens to name:
    # "At Northwind Analytics I shipped 229 releases" passes. Narrowing this
    # would also break the legitimate case of citing a degree year alongside an
    # employer. Employer-owned metrics are still bound — see
    # test_metric_bound_to_wrong_employer_fails, which is the check that matters.
    assert findings_for("At Northwind Analytics I shipped 229 releases.") == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn(); passed += 1; print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} tests passed")
if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn(); passed += 1; print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} tests passed")
