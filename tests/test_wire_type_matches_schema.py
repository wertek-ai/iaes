"""`IAESWireEnvelope` must relax exactly the fields the schema relaxes.

The TypeScript SDK carries two envelope types: `IAESEnvelope`, which describes
what the SDK PRODUCES, and `IAESWireEnvelope`, which describes what may ARRIVE.
The second exists because the schema is looser than the first, and it is only
useful if it is looser in exactly the right places.

It was not, twice, and each time the gap was found by a person reading rather
than by anything mechanical:

  content_hash      the schema does not list it in `required`, so a conforming
                    producer may omit it -- and the type demanded it.
  source_event_id   the schema types it ["string", "null"], so an explicit null
                    is a valid 2.0 event -- and the type admitted only string.

Fixing one at a time is how the second one survived the first review. This
compares EVERY property of the schema against the interface, so a third would
be found by the suite rather than by luck.

It reads the TypeScript as text on purpose. Parsing it properly would mean a
TypeScript toolchain inside a Python test, and the shape being checked --
`name?:` and `| null` -- is simple enough that a regex is honest about what it
can and cannot see. What it cannot see is stated in `unchecked` below.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema" / "iaes-envelope.schema.json"
ENVELOPE_TS = ROOT / "npm" / "src" / "envelope.ts"


def interface_body(name: str) -> str:
    text = ENVELOPE_TS.read_text(encoding="utf-8")
    start = text.index(f"export interface {name}")
    return text[start:text.index("\n}\n", start)]


def declared_fields(body: str) -> dict:
    """{field: (optional, admits_null)} as the interface declares them."""
    out = {}
    for m in re.finditer(r"^\s{2}([a-z_]+)(\??):\s*([^;]+);", body, re.M):
        name, question, type_text = m.group(1), m.group(2), m.group(3)
        out[name] = (question == "?", "null" in type_text)
    return out


def wire_overrides() -> dict:
    """The fields IAESWireEnvelope redeclares, and how."""
    text = ENVELOPE_TS.read_text(encoding="utf-8")
    m = re.search(r"export type IAESWireEnvelope = Omit<(.*?)>\s*&\s*\{(.*?)\};",
                  text, re.S)
    assert m, "IAESWireEnvelope is not declared in the form this test reads"
    omitted = set(re.findall(r'"([a-z_]+)"', m.group(1)))
    redeclared = {}
    for f in re.finditer(r"^\s{2}([a-z_]+)(\??):\s*([^;]+);", m.group(2), re.M):
        redeclared[f.group(1)] = (f.group(2) == "?", "null" in f.group(3))
    assert omitted == set(redeclared), (
        f"IAESWireEnvelope omits {sorted(omitted)} and redeclares "
        f"{sorted(redeclared)}; a field omitted and not redeclared disappears "
        f"from the type"
    )
    return redeclared


def schema_expectations() -> dict:
    """{field: (may_be_omitted, may_be_null)} as the schema states them."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    required = set(schema.get("required", []))
    out = {}
    for name, spec in schema["properties"].items():
        types = spec.get("type")
        types = types if isinstance(types, list) else ([types] if types else [])
        out[name] = (name not in required, "null" in types)
    return out


def test_the_wire_type_matches_the_schema_field_by_field():
    produced = declared_fields(interface_body("IAESEnvelope"))
    overrides = wire_overrides()
    expected = schema_expectations()

    wrong = []
    for name, (may_omit, may_be_null) in sorted(expected.items()):
        if name not in produced:
            continue                       # not modelled; a different problem
        optional, admits_null = overrides.get(name, produced[name])
        if (optional, admits_null) != (may_omit, may_be_null):
            wrong.append(
                f"{name}: schema says may_omit={may_omit} may_be_null="
                f"{may_be_null}, IAESWireEnvelope says optional={optional} "
                f"admits_null={admits_null}"
            )
    assert not wrong, (
        "IAESWireEnvelope does not match the wire contract:\n  "
        + "\n  ".join(wrong)
    )


def test_the_produced_type_is_not_relaxed_by_accident():
    """Relaxing the wire type must not relax what the SDK promises it emits.

    `IAESEnvelope` is the published API. Every field this SDK always sets stays
    required and non-null there, whatever the schema permits, because code that
    reads those fields without a null check already compiles.
    """
    produced = declared_fields(interface_body("IAESEnvelope"))
    assert produced["content_hash"] == (False, False), (
        "content_hash must stay required and non-null on IAESEnvelope: every "
        "toJSON() sets it, and weakening it breaks e.content_hash.slice(0, 8)"
    )
    assert produced["source_event_id"] == (True, False), (
        "source_event_id is optional and never null on a produced envelope: "
        "this SDK omits it rather than emitting null"
    )


def test_what_this_check_cannot_see():
    """Stated rather than discovered.

    The interface is read as text, so this checks OPTIONALITY and whether the
    declared type mentions null. It does not check that the underlying type is
    right -- a field typed `number` where the schema says `string` would pass
    -- and it does not follow `Omit`/`Pick` chains beyond the one form
    IAESWireEnvelope uses, which is why wire_overrides() asserts that form.
    """
    body = interface_body("IAESEnvelope")
    assert "content_hash" in body and "source_event_id" in body
