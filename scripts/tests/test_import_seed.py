"""
Offline tests for the try-page seed importer. No network, fictional data only.
Run:  python scripts/tests/test_import_seed.py   (or python -m pytest -q)

The contract, and the first two matter far more than the rest:

  - it NEVER writes through a symlink. sync-private.sh links career_facts.yaml at a separate
    private repo, and write_text() follows a symlink: importing over one would overwrite a
    real, human-verified history with a model's reading of a CV.
  - `verified` is forced to false on import, even if the seed claims otherwise. Verification
    means a human read the file; a flag arriving pre-set would be a claim nobody made.
  - it refuses to overwrite existing files without --force
  - a malformed or non-seed JSON file is refused, not half-imported
  - --dry-run writes nothing
"""
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "import-seed.py"

SEED = {
    "career_facts": {
        "candidate": {"name": "Jordan Vale", "location": "Lisbon",
                      "contact": {"email": "j@example.com", "phone": "", "linkedin": ""}},
        "employers": [{"company": "Northwind Freight", "title": "Senior PM",
                       "start": "2021-03", "end": "2025-08",
                       "metrics": ["Cut close from 6 days to 1"], "scope": []}],
        "education": [], "certifications": [], "skills": [],
    },
    "cv_source": "# Jordan Vale\n\nSenior PM at Northwind Freight.\n",
}


def sandbox(tmp: Path) -> Path:
    """A throwaway repo shaped like the real one, so the script's REPO-relative paths land here."""
    (tmp / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp / "profile").mkdir(parents=True, exist_ok=True)
    (tmp / "scripts" / "import-seed.py").write_text(SCRIPT.read_text(encoding="utf-8"),
                                                    encoding="utf-8")
    return tmp / "scripts" / "import-seed.py"


def run(script: Path, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True, cwd=str(script.parents[1]))


def write_seed(tmp: Path, data=None) -> Path:
    p = tmp / "seed.json"
    p.write_text(json.dumps(data if data is not None else SEED), encoding="utf-8")
    return p


def test_a_clean_import_writes_both_files():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); script = sandbox(tmp); seed = write_seed(tmp)
        r = run(script, str(seed))
        assert r.returncode == 0, r.stderr
        facts = (tmp / "career_facts.yaml").read_text(encoding="utf-8")
        assert "Northwind Freight" in facts
        assert "NOT YET VERIFIED BY A HUMAN" in facts
        assert "Jordan Vale" in (tmp / "profile" / "05-cv-source.md").read_text(encoding="utf-8")


def test_verified_is_forced_false_even_if_the_seed_claims_true():
    """Verification is a human reading the file. A pre-set flag is a claim nobody made."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); script = sandbox(tmp)
        lying = json.loads(json.dumps(SEED))
        lying["career_facts"]["verified"] = True
        seed = write_seed(tmp, lying)
        assert run(script, str(seed)).returncode == 0
        assert "verified: false" in (tmp / "career_facts.yaml").read_text(encoding="utf-8")


def test_it_never_writes_through_a_symlink():
    """The one that actually matters. sync-private.sh links these paths at a private repo, and
    write_text() follows a symlink, so this is the difference between an import and a loss."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); script = sandbox(tmp); seed = write_seed(tmp)
        real = tmp / "elsewhere.yaml"
        real.write_text("# my real, verified history\nverified: true\n", encoding="utf-8")
        os.symlink(real, tmp / "career_facts.yaml")

        r = run(script, str(seed))
        assert r.returncode == 1, "must refuse when the target is a symlink"
        assert "already exist" in r.stderr
        assert real.read_text(encoding="utf-8").startswith("# my real")

        # Even under --force, the symlink is replaced and its target left alone.
        r = run(script, str(seed), "--force")
        assert r.returncode == 0, r.stderr
        assert real.read_text(encoding="utf-8").startswith("# my real"), \
            "--force must replace the link, never write through it"
        assert not (tmp / "career_facts.yaml").is_symlink()
        assert "Northwind" in (tmp / "career_facts.yaml").read_text(encoding="utf-8")


def test_it_refuses_to_overwrite_without_force():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); script = sandbox(tmp); seed = write_seed(tmp)
        (tmp / "career_facts.yaml").write_text("verified: true\nreal: yes\n", encoding="utf-8")
        r = run(script, str(seed))
        assert r.returncode == 1 and "already exist" in r.stderr
        assert "real: yes" in (tmp / "career_facts.yaml").read_text(encoding="utf-8")


def test_dry_run_writes_nothing():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); script = sandbox(tmp); seed = write_seed(tmp)
        r = run(script, str(seed), "--dry-run")
        assert r.returncode == 0 and "Dry run" in r.stdout
        assert "Northwind Freight" in r.stdout, "should summarise what it would write"
        assert not (tmp / "career_facts.yaml").exists()


def test_a_file_that_is_not_a_seed_is_refused():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); script = sandbox(tmp)
        for bad in ('{"something": "else"}', "not json at all", "[]"):
            p = tmp / "bad.json"; p.write_text(bad, encoding="utf-8")
            r = run(script, str(p))
            assert r.returncode == 1, f"should refuse: {bad[:20]}"
            assert not (tmp / "career_facts.yaml").exists()


def test_a_missing_file_is_refused_cleanly():
    with tempfile.TemporaryDirectory() as d:
        script = sandbox(Path(d))
        r = run(script, "/nonexistent/seed.json")
        assert r.returncode == 1 and "No such file" in r.stderr


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"  ok    {name}")
            except AssertionError as exc:
                failures += 1; print(f"  FAIL  {name}  {exc}")
    print()
    print("all import-seed tests passed" if not failures else f"{failures} test(s) failed")
    sys.exit(1 if failures else 0)
