"""Armed at zero: seven ways to break the registry, and the repair each names.

The messages matter as much as the failures. A guard is not correct merely
because it rejects the bad state -- its canonical repair must also preserve the
invariant. The multi-part case proves it: "not in the registry" is true and
teaches a reader to add an entry for a family whose availability cannot be
answered, which would institutionalise the next defect.

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
        REGISTRY.write_text(json.dumps(d, indent=2), encoding="utf-8", newline="\n")
        return run()

    try:
        yield edit
    finally:
        REGISTRY.write_text(original, encoding="utf-8", newline="\n")


@pytest.fixture
def spec():
    original = SPEC.read_text(encoding="utf-8")

    def replace(old: str, new: str):
        assert old in original, f"the specification no longer contains {old!r}"
        SPEC.write_text(original.replace(old, new, 1), encoding="utf-8", newline="\n")
        return run()

    try:
        yield replace
    finally:
        SPEC.write_text(original, encoding="utf-8", newline="\n")


def entry(d: dict, entry_id: str) -> dict:
    for e in d["references"]:
        if e["id"] == entry_id:
            return e
    raise AssertionError(f"{entry_id} is no longer in the registry")


def test_the_repository_is_clean():
    r = run()
    assert r.returncode == 0, r.stdout + r.stderr


def test_it_scans_every_normative_artifact_not_one_table():
    """The earlier version read only the References section of the
    specification -- a table we maintain -- and so missed what GOVERNANCE.md
    cites and what the schemas declare as their dialect."""
    r = run()
    assert r.returncode == 0
    # RFC 9745 and RFC 8594 appear only in GOVERNANCE.md; the JSON Schema
    # dialect appears only in $schema. All three are accounted for.
    d = json.loads(REGISTRY.read_text(encoding="utf-8"))
    declared = {e["cited_as"] for e in d["references"]}
    assert "RFC 9745" in declared and "RFC 8594" in declared
    assert any(c.startswith("https://json-schema.org/") for c in declared)


def test_a_cited_document_that_is_not_declared_fails(registry):
    def drop_rfc3339(d):
        d["references"] = [e for e in d["references"] if e["cited_as"] != "RFC 3339"]

    r = registry(drop_rfc3339)
    assert r.returncode == 1
    assert "is not declared in references/registry.json" in r.stderr
    assert "availability" in r.stderr, "the message should say what to add"


def test_a_held_copy_must_say_which_copy(registry):
    """An edition is part of the evidence's identity, not decoration."""
    def drop_edition(d):
        entry(d, "ISO-14224:2016-en").pop("edition")

    r = registry(drop_edition)
    assert r.returncode == 1
    assert "`edition` is missing" in r.stderr
    assert "names a family, not evidence" in r.stderr


def test_identity_comes_before_possession(registry):
    """An ISO citation with no edition names a family. Recording it available
    or unavailable answers a question that cannot yet be asked."""
    def claim_available(d):
        e = entry(d, "ISO-17359-unpinned")
        e["availability"] = "available"
        e["edition"], e["language"], e["access_basis"] = "2018", "en", "steward_copy"

    r = registry(claim_available)
    assert r.returncode == 1
    assert "names no edition" in r.stderr
    assert "cannot yet be asked" in r.stderr
    assert "`unresolved`" in r.stderr, "the message should name the right value"


def test_a_mention_without_a_reason_fails(registry):
    """Declaring something a mention is a decision, so it carries a reason."""
    def blank_reason(d):
        d["mentions_not_dependencies"]["ISO 8601"] = ""

    r = registry(blank_reason)
    assert r.returncode == 1
    assert "no reason" in r.stderr


def test_a_declaration_nothing_cites_fails(registry):
    """A registry that outlives its citations stops describing the standard."""
    def add_orphan(d):
        d["references"].append({
            "id": "ISO-9001", "publisher": "ISO", "number": "9001",
            "availability": "public", "cited_as": "ISO 9001",
        })

    r = registry(add_orphan)
    assert r.returncode == 1
    assert "cited by no normative artifact" in r.stderr


def test_a_duplicate_key_is_refused_rather_than_resolved():
    """Python keeps the last duplicate silently: two truths, one chosen by
    nobody. The registry decides what IAES may cite, so it must not."""
    original = REGISTRY.read_text(encoding="utf-8")
    try:
        REGISTRY.write_text(
            original.replace('"registry_version": 1,',
                             '"registry_version": 1,\n  "registry_version": 2,', 1),
            encoding="utf-8", newline="\n")
        r = run()
        assert r.returncode == 1
        assert "twice" in r.stderr
    finally:
        REGISTRY.write_text(original, encoding="utf-8", newline="\n")


def test_a_multipart_standard_cited_without_a_part_fails(spec):
    # ISO 61508 rather than 13374: the latter is a declared mention, and a
    # mention exemption masks the check for that name. See the guard's note on
    # that limit.
    r = spec("| ISO 13374 series | No. Mentioned",
             "| ISO 61508 | No. Mentioned")
    assert r.returncode == 1
    assert "does not identify a document" in r.stderr
    assert "series" in r.stderr, "the message should offer the family form"
    assert "Do not add a registry entry" in r.stderr, (
        "the canonical repair must not be the wrong one")


def test_it_does_not_claim_to_check_support():
    """The third rung is not this one, and the output says so."""
    r = run()
    assert "not checked here" in r.stdout
    assert "attributes to it" in r.stdout
