"""Three documents describe the envelope. They must say the same thing.

The schema decides -- it is what a validator runs. `IAES_SPEC.md` is what people
read. `rfc/IAES-RFC-001.md` is the rationale, which RFC-000 demoted from
authority precisely because it can fall behind.

Falling behind is not harmless. Until 2026-09-06 the RFC marked
`correlation_id` OPTIONAL while the schema and the specification had required it
since 1.0, and the Arduino Opta reference runtime followed the rationale: every
event it ever emitted was missing a required field, and the standard's own
validator rejected all of them.

A document that is not authoritative is still read.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

ENVELOPE = json.loads((ROOT / "schema" / "iaes-envelope.schema.json").read_text(encoding="utf-8"))
SPEC = (ROOT / "IAES_SPEC.md").read_text(encoding="utf-8")
RFC = (ROOT / "rfc" / "IAES-RFC-001.md").read_text(encoding="utf-8")

# Fields a document may legitimately not mention, with the reason.
NOT_IN_RFC = {
    "dataschema": "added in 1.4; RFC-001 was written for 1.0 and RFC-000 "
                  "declares an incorporated RFC to be rationale, not authority",
}


def schema_required() -> set[str]:
    return set(ENVELOPE["required"])


def schema_fields() -> set[str]:
    return set(ENVELOPE["properties"])


def spec_required() -> dict[str, bool]:
    """The `yes`/`no` column of the envelope table in IAES_SPEC.md."""
    return {name: col == "yes"
            for name, col in re.findall(r"^\| `(\w+)` \| [^|]+ \| (yes|no) \|", SPEC, re.M)}


def rfc_required() -> dict[str, bool]:
    """The (REQUIRED)/(OPTIONAL) marker on each envelope section of RFC-001."""
    return {name: word == "REQUIRED"
            for name, word in re.findall(r"^#+ [\d.]+\. (\w+) \((REQUIRED|OPTIONAL)\)", RFC, re.M)}


SPEC_SAYS = spec_required()
RFC_SAYS = rfc_required()


@pytest.mark.parametrize("field", sorted(schema_fields()))
def test_the_specification_agrees_with_the_schema(field):
    assert field in SPEC_SAYS, f"IAES_SPEC.md does not document the envelope's {field}"
    assert SPEC_SAYS[field] == (field in schema_required()), (
        f"{field}: the schema says "
        f"{'required' if field in schema_required() else 'optional'} and "
        f"IAES_SPEC.md says {'required' if SPEC_SAYS[field] else 'optional'}")


@pytest.mark.parametrize("field", sorted(schema_fields()))
def test_the_rationale_agrees_with_the_schema(field):
    if field not in RFC_SAYS:
        assert field in NOT_IN_RFC, (
            f"RFC-001 does not describe the envelope's {field}, and nothing says why")
        return
    assert RFC_SAYS[field] == (field in schema_required()), (
        f"{field}: the schema says "
        f"{'required' if field in schema_required() else 'optional'} and "
        f"RFC-001 says {'REQUIRED' if RFC_SAYS[field] else 'OPTIONAL'}. "
        f"The schema decides; the RFC is rationale, and rationale that "
        f"contradicts the contract gets followed anyway.")


def test_the_rfc_describes_no_field_the_schema_does_not_have():
    extra = set(RFC_SAYS) - schema_fields()
    assert not extra, (
        f"RFC-001 describes envelope fields the schema does not define: "
        f"{sorted(extra)}")


@pytest.mark.parametrize("field", sorted(NOT_IN_RFC))
def test_an_excused_field_is_still_missing(field):
    """An excuse that stops being true is a lie that nobody re-reads."""
    assert field in schema_fields(), f"{field} is no longer an envelope field"
    assert field not in RFC_SAYS, (
        f"RFC-001 now describes {field}. Drop it from NOT_IN_RFC.")
