"""The Ignition scenario's RFC 8785 serialiser against every shared JCS vector.

`scenarios/ignition/build_tags.py` carries its own serialiser (`canonical`,
`jcs_string`, `jcs_number`), because the Gateway runs Jython 2.7 and the SDK is
not installed there. `tests/test_reference_scenarios.py` runs the whole script,
but the reference story is ASCII with ordinary numbers, so it exercises almost
none of RFC 8785. This runs the serialiser itself over every `jcs` entry of
`conformance/content_hash.json`, the same vectors the two SDKs run.

What this proves and what it does not: it runs the script's code on CPython 3.
Jython 2.7 is not available here, and the hash depends on how `repr` writes
floats, how `float()` rounds a long and how text is stored (UTF-16 in Jython).
Those were measured on a real Gateway for the vectors that existed on
2026-10-07 (14 of 14, scenarios/ignition/README.md); vectors added later must be
re-measured there before that claim covers them.
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HASHES = json.loads((ROOT / "conformance" / "content_hash.json").read_text(encoding="utf-8"))["cases"]

#: The serialiser starts where the script decides how text and integers are
#: represented, and ends where the event building starts. Anchored on those
#: two statements, and the test fails loudly if either moves.
_START = "try:\n\tTEXT = unicode"
_END = "def stamp():"
_NAMES = ("well_formed", "jcs_string", "jcs_number", "canonical", "content_hash")


def _serialiser() -> dict:
    sys.path.insert(0, str(ROOT / "scenarios" / "ignition"))
    try:
        import build_tags
    finally:
        sys.path.pop(0)
    script = build_tags.SCRIPT
    assert script.count(_START) == 1, f"the script no longer has exactly one {_START!r}"
    assert script.count(_END) == 1, f"the script no longer has exactly one {_END!r}"
    start, end = script.index(_START), script.index(_END)
    assert start < end, "the serialiser is no longer before the event building"
    namespace = {"hashlib": hashlib}
    exec(compile(script[start:end], "build_tags.SCRIPT[serialiser]", "exec"), namespace)
    missing = [n for n in _NAMES if not callable(namespace.get(n))]
    assert not missing, f"the extracted serialiser lacks {missing}"
    return namespace


SERIALISER = _serialiser()
ACCEPTED = [c for c in HASHES if not c["jcs"].get("reject")]
REFUSED = [c for c in HASHES if c["jcs"].get("reject")]


def test_every_kind_of_vector_is_here():
    """Control: no refusal, or no accepted vector, would prove nothing about that side."""
    assert ACCEPTED and REFUSED
    assert len(ACCEPTED) + len(REFUSED) == len(HASHES)


@pytest.mark.parametrize("case", ACCEPTED, ids=[c["id"] for c in ACCEPTED])
def test_ignition_writes_the_jcs_bytes(case):
    assert SERIALISER["canonical"](case["data"]) == case["jcs"]["canonical"], case["title"]
    assert SERIALISER["content_hash"](case["data"]) == case["jcs"]["content_hash"], case["title"]


@pytest.mark.parametrize("case", REFUSED, ids=[c["id"] for c in REFUSED])
def test_ignition_refuses_what_jcs_cannot_serialise(case):
    with pytest.raises(ValueError):
        SERIALISER["canonical"](case["data"])
