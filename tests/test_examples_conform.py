"""Every event this repository shows as an example conforms to the specification.

An example is copied more than any paragraph is read. On 2026-10-06 a review
found six events in examples/ whose identifiers were UUID-shaped with a non-hex
first digit ("h1a2b3c4-..."), and a Node-RED example flow carrying a 1.2 event
with event_id "example-001" and no correlation_id. tests/test_validation.py
validated those files and passed, because the schemas only annotate `format`.

So examples are judged by both verdicts of conformance/README.md: the schema,
and find_nonconformities.
"""

import json
from pathlib import Path

import pytest

from iaes import ValidationError, find_nonconformities, validate

ROOT = Path(__file__).resolve().parent.parent
SOURCES = sorted(
    list((ROOT / "examples").glob("*.json"))
    + list((ROOT / "node-red" / "examples").glob("*.json"))
)


def _events(obj):
    """Events in a file: objects that look like envelopes, and JSON strings that hold one."""
    if isinstance(obj, dict):
        if "event_type" in obj and "event_id" in obj:
            yield obj
        for value in obj.values():
            yield from _events(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _events(value)
    elif isinstance(obj, str) and obj.lstrip().startswith("{") and '"event_type"' in obj:
        try:
            yield from _events(json.loads(obj))
        except ValueError:
            pass


EVENTS = [
    (f"{path.relative_to(ROOT).as_posix()}#{i}", event)
    for path in SOURCES
    for i, event in enumerate(_events(json.loads(path.read_text(encoding="utf-8"))))
]


def test_examples_were_found():
    # Control: if the walk stopped finding events, every test below would pass on nothing.
    assert len(EVENTS) >= 20
    assert any(name.startswith("node-red/examples/") for name, _ in EVENTS)


@pytest.mark.parametrize("name,event", EVENTS, ids=[n for n, _ in EVENTS])
def test_an_example_event_conforms(name, event):
    try:
        validate(event)
    except ValidationError as e:
        pytest.fail(f"{name} is rejected by the schema: {e}")
    assert find_nonconformities(event) == [], f"{name} breaks the specification"
