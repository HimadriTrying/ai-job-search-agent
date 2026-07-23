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
            "scope": ["Owned roadmap for 3 squads, ~25 engineers"],
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


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn(); passed += 1; print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} tests passed")
