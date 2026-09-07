"""Armed at zero: five ways to break the registry, and the repair each names.

The messages matter as much as the failures. A guard for a public standard is
read by contributors who did not write it, so each one says what broke, why it
is wrong, and how to write it correctly.

SPDX-License-Identifier: CC-BY-4.0
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GUARD = ROOT / "tools" / "check_document_available.py"
REGISTRY = ROOT / "references" / "registry.json"
SPEC = ROOT / "IAES_SPEC.md"


def run() -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GUARD)],
                          cwd=ROOT, capture_output=True, text=True)


@pytest.fixture
def registry():
    """Edits the registry through a callable, and always restores it."""
    original = REGISTRY.read_text(encoding="utf-8")

    def edit(fn):
        d = json.loads(original)
        fn(d)
        REGISTRY.write_text(json.dumps(d, indent=2), encoding="utf-8")
        return run()

    try:
        yield edit
    finally:
        REGISTRY.write_text(original, encoding="utf-8")


@pytest.fixture
def spec():
    original = SPEC.read_text(encoding="utf-8")

    def replace(old: str, new: str):
        assert old in original, f"the specification no longer contains {old!r}"
        SPEC.write_text(original.replace(old, new, 1), encoding="utf-8")
        return run()

    try:
        yield replace
    finally:
        SPEC.write_text(original, encoding="utf-8")


def test_the_repository_is_clean():
    r = run()
    assert r.returncode == 0, r.stdout + r.stderr


def test_a_cited_document_that_is_not_declared_fails(registry):
    def drop_rfc3339(d):
        d["references"] = [e for e in d["references"] if e["cited_as"] != "RFC 3339"]

    r = registry(drop_rfc3339)
    assert r.returncode == 1
    assert "does not declare" in r.stderr
    assert "availability" in r.stderr, "the message should say what to add"


def test_a_held_copy_must_say_which_copy(registry):
    """An edition is part of the evidence's identity, not decoration."""
    def drop_edition(d):
        for e in d["references"]:
            if e["id"].startswith("ISO-14224"):
                e.pop("edition")

    r = registry(drop_edition)
    assert r.returncode == 1
    assert "`edition` is missing" in r.stderr
    assert "names a family, not evidence" in r.stderr


def test_a_declaration_nothing_cites_fails(registry):
    """A registry that outlives its citations stops describing the standard."""
    def add_orphan(d):
        d["references"].append({
            "id": "ISO-9001", "publisher": "ISO", "number": "9001",
            "availability": "public", "cited_as": "ISO 9001",
        })

    r = registry(add_orphan)
    assert r.returncode == 1
    assert "cited nowhere" in r.stderr


def test_a_duplicate_key_is_refused_rather_than_resolved():
    """Python keeps the last duplicate silently: two truths, one chosen by
    nobody. The registry decides what IAES may cite, so it must not."""
    original = REGISTRY.read_text(encoding="utf-8")
    try:
        REGISTRY.write_text(
            original.replace('"registry_version": 1,',
                             '"registry_version": 1,\n  "registry_version": 2,', 1),
            encoding="utf-8")
        r = run()
        assert r.returncode == 1
        assert "twice" in r.stderr
    finally:
        REGISTRY.write_text(original, encoding="utf-8")


def test_a_multipart_standard_cited_without_a_part_fails(spec):
    r = spec("| ISO 13374 series |", "| ISO 13374 |")
    assert r.returncode == 1
    assert "does not identify a document" in r.stderr
    assert "series" in r.stderr, "the message should offer the family form"


def test_it_does_not_claim_to_check_support():
    """The third rung is not this one, and the output says so."""
    r = run()
    assert "not checked here" in r.stdout
    assert "attributes to it" in r.stdout
