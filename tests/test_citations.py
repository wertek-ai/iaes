"""Armed at zero, including the controls that keep it from crying wolf.

A guard that has never been seen to fail has not been shown to work, and one
that fires on correct text gets switched off. Both halves are tested here.

SPDX-License-Identifier: CC-BY-4.0
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GUARD = ROOT / "tools" / "check_citations.py"
GOVERNANCE = ROOT / "GOVERNANCE.md"


def run() -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GUARD)],
                          cwd=ROOT, capture_output=True, text=True)


@pytest.fixture
def appended():
    """Adds a line to GOVERNANCE.md, and always puts it back."""
    original = GOVERNANCE.read_text(encoding="utf-8")

    def add(line: str):
        GOVERNANCE.write_text(original + "\n" + line + "\n", encoding="utf-8", newline="\n")
        return run()

    try:
        yield add
    finally:
        GOVERNANCE.write_text(original, encoding="utf-8", newline="\n")


def test_the_repository_is_clean():
    r = run()
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.parametrize("line,why", [
    ("A broken citation: GOVERNANCE.md §9.9 does not exist.",
     "the section-sign form"),
    ("See IAES_SPEC.md section 88.1 for details.",
     "the word 'section' instead of the sign"),
    ("Per RFC-001 §77.7 this applies.",
     "one of our own RFCs, cited by its short name"),
])
def test_a_citation_to_nothing_fails(appended, line, why):
    r = appended(line)
    assert r.returncode == 1, f"{why}: the guard let it through"
    assert "does not exist" in r.stderr


def test_the_hint_names_the_section_that_does_exist(appended):
    """The real mistake is writing 'section N, item M' as '§N.M'."""
    r = appended("Wrongly cited: GOVERNANCE.md §1.2.")
    assert r.returncode == 1
    assert "§1 exists" in r.stderr and "item N" in r.stderr


@pytest.mark.parametrize("line,why", [
    ("HTTP/2 is defined in RFC-9113 §1.2, which is not ours.",
     "an IETF RFC has no file in rfc/, so it is not a citation of ours"),
    ("See GOVERNANCE.md §4.2, which does exist.",
     "a citation that resolves"),
    ("GOVERNANCE.md §3-bis covers releases.",
     "a section number that is not purely numeric"),
])
def test_it_does_not_cry_wolf(appended, line, why):
    r = appended(line)
    assert r.returncode == 0, f"false positive on {why}:\n{r.stderr}"
