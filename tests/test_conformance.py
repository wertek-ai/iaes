"""The Python SDK against the shared conformance cases (conformance/).

The same cases run in the TypeScript SDK, the Node-RED nodes and the n8n
nodes. Agreement between implementations is what this suite exists to make
measurable; see conformance/README.md.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from iaes import ValidationError, canonical_json, compute_content_hash, find_nonconformities, validate

ROOT = Path(__file__).resolve().parent.parent
CASES = json.loads((ROOT / "conformance" / "validation.json").read_text(encoding="utf-8"))["cases"]
HASHES = json.loads((ROOT / "conformance" / "content_hash.json").read_text(encoding="utf-8"))["cases"]


def test_the_cases_are_generated_not_edited():
    """The JSON is generated; a hand edit would drift from the generator."""
    out = subprocess.run(
        [sys.executable, "tools/build_conformance_cases.py", "--check"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr


def test_the_suite_has_each_kind_of_case():
    """Control: a suite with no rejected or no nonconforming case proves nothing."""
    kinds = {(c["expect"]["schema_valid"], c["expect"]["conforming"]) for c in CASES}
    assert kinds == {(True, True), (False, False), (True, False)}


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_schema_verdict(case):
    # Anything other than ValidationError -- AttributeError, KeyError -- is a
    # crash, not a verdict, and fails the test as an error.
    try:
        validate(case["event"])
        got = True
    except ValidationError:
        got = False
    assert got is case["expect"]["schema_valid"], case["title"]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_nonconforming_fields(case):
    if not case["expect"]["schema_valid"]:
        pytest.skip("rejected by the schema; its fields are not judged one by one")
    assert find_nonconformities(case["event"]) == case["expect"]["nonconforming_fields"], case["title"]


@pytest.mark.parametrize("case", [c for c in HASHES if c["status"] != "jcs_only"],
                         ids=[c["id"] for c in HASHES if c["status"] != "jcs_only"])
def test_content_hash_2_0(case):
    """2.0 events keep the 2.0 rule (IAES-RFC-011 §5): what this SDK produced before."""
    expected = (case["content_hash"] if case["status"] == "agreed"
                else case["by_implementation"]["python"]["content_hash"])
    assert compute_content_hash(case["data"], "2.0") == expected, case["title"]


@pytest.mark.parametrize("case", HASHES, ids=[c["id"] for c in HASHES])
def test_content_hash_2_1_is_jcs(case):
    """2.1 and later hash RFC 8785 (JCS): the same bytes in every implementation."""
    assert canonical_json(case["data"]) == case["jcs"]["canonical"], case["title"]
    assert compute_content_hash(case["data"], "2.1") == case["jcs"]["content_hash"], case["title"]
