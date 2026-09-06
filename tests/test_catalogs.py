"""The schemas close ten catalogs. The SDKs publish ten. They are not the same ten.

A closed enumeration is a promise in two places at once: the schema rejects
anything outside it, and the SDK is where a producer reads what is allowed. When
those two drift, nothing fails -- the producer simply cannot discover a value
that the schema will demand, or trusts a list the schema never agreed to.

Measured 2026-09-06, they disagree in both directions at once:

    triggered_by      closed in the schema, no enumeration published
    MeasurementType   published by the SDKs, open in the schema

Neither is a bug to fix here. Both are decisions for IAES 1.5, and each is
declared below with the reason and where it gets resolved -- so the count is a
measurement rather than a recollection when that RFC is written.
"""

import enum
import glob
import inspect
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Schema field -> SDK enumeration. Explicit, because guessing the pairing from
# the names is how a rename stops being noticed.
PAIRS = {
    "condition_trend": "ConditionTrend",
    "hierarchy_level": "HierarchyLevel",
    "iso_13374_status": "ISO13374Status",
    "priority": "WorkOrderPriority",
    "registration_status": "RegistrationStatus",
    "relationship_type": "RelationshipType",
    "severity": "Severity",
    "status": "CompletionStatus",
    "units_qualifier": "UnitsQualifier",
}

# Closed in the schema, with no enumeration for a producer to read.
UNPUBLISHED = {
    "triggered_by": {
        "why": "A producer must send one of five values and has no published "
               "list to read them from. Closed in the schema since 1.0.",
        "resolve_in": "1.5",
    },
}

# Published by the SDKs over a field the schema leaves open.
ADVISORY = {
    "MeasurementType": {
        "field": "measurement_type",
        "why": "The schema carries examples, not an enum, so this list is a "
               "convenience and not a constraint. It must never be presented "
               "as one: an implementation that rejects an unlisted measurement "
               "type is stricter than the standard.",
        "resolve_in": "1.5",
    },
}


def schema_enums() -> dict[str, list]:
    found = {}
    for f in sorted(glob.glob(str(ROOT / "schema" / "*.schema.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        props = d.get("properties", {})
        if "data" in props and "properties" in props["data"]:
            props = props["data"]["properties"]
        for k, v in props.items():
            if isinstance(v, dict) and "enum" in v:
                found[k] = sorted(x for x in v["enum"] if x is not None)
    return found


def python_enums() -> dict[str, list]:
    import iaes
    return {n: sorted(m.value for m in o) for n, o in vars(iaes).items()
            if inspect.isclass(o) and issubclass(o, enum.Enum)}


def typescript_enums() -> dict[str, list]:
    src = (ROOT / "npm" / "src" / "enums.ts").read_text(encoding="utf-8")
    found = {}
    for name, body in re.findall(r"export const (\w+) = \{(.*?)\} as const", src, re.S):
        found[name] = sorted(re.findall(r':\s*"([^"]+)"', body))
    return found


SCHEMA = schema_enums()
PYTHON = python_enums()
TYPESCRIPT = typescript_enums()


# ─── the two sides must agree, value for value ───────────────

@pytest.mark.parametrize("field,cls", sorted(PAIRS.items()))
def test_python_publishes_exactly_what_the_schema_closes(field, cls):
    assert field in SCHEMA, f"{field} is no longer a closed enum in any schema"
    assert cls in PYTHON, f"the SDK no longer publishes {cls}"
    assert PYTHON[cls] == SCHEMA[field], (
        f"{cls} and the schema's {field} disagree.\n"
        f"  only in the SDK   : {sorted(set(PYTHON[cls]) - set(SCHEMA[field]))}\n"
        f"  only in the schema: {sorted(set(SCHEMA[field]) - set(PYTHON[cls]))}")


@pytest.mark.parametrize("field,cls", sorted(PAIRS.items()))
def test_typescript_publishes_the_same_values(field, cls):
    assert cls in TYPESCRIPT, f"the TypeScript SDK no longer publishes {cls}"
    assert TYPESCRIPT[cls] == SCHEMA[field], (
        f"TypeScript's {cls} and the schema's {field} disagree.\n"
        f"  only in the SDK   : {sorted(set(TYPESCRIPT[cls]) - set(SCHEMA[field]))}\n"
        f"  only in the schema: {sorted(set(SCHEMA[field]) - set(TYPESCRIPT[cls]))}")


def test_the_two_sdks_publish_the_same_catalogs():
    """A value an integrator can send from one language and not the other."""
    assert set(PYTHON) == set(TYPESCRIPT), (
        f"only in Python: {sorted(set(PYTHON) - set(TYPESCRIPT))}, "
        f"only in TypeScript: {sorted(set(TYPESCRIPT) - set(PYTHON))}")
    for name in sorted(PYTHON):
        assert PYTHON[name] == TYPESCRIPT[name], f"{name} differs between the SDKs"


# ─── and nothing may drift in unannounced ────────────────────

def test_every_closed_schema_enum_is_paired_or_declared():
    unaccounted = set(SCHEMA) - set(PAIRS) - set(UNPUBLISHED)
    assert not unaccounted, (
        f"closed in a schema and neither published nor declared: "
        f"{sorted(unaccounted)}. A producer has no list to read them from.")


def test_every_sdk_enum_is_paired_or_declared_advisory():
    unaccounted = set(PYTHON) - set(PAIRS.values()) - set(ADVISORY)
    assert not unaccounted, (
        f"published by the SDK over nothing the schema closes: "
        f"{sorted(unaccounted)}. Either the schema closes it, or it is declared "
        f"advisory so nobody mistakes it for a constraint.")


@pytest.mark.parametrize("field", sorted(UNPUBLISHED))
def test_an_unpublished_catalog_is_still_unpublished(field):
    """Declared gaps that get filled must stop being declared."""
    assert field in SCHEMA, f"{field} is no longer closed; drop it from UNPUBLISHED"
    guess = "".join(w.capitalize() for w in field.split("_"))
    assert guess not in PYTHON, (
        f"{field} now has {guess} in the SDK. Move it to PAIRS.")


@pytest.mark.parametrize("cls", sorted(ADVISORY))
def test_an_advisory_catalog_is_still_advisory(cls):
    field = ADVISORY[cls]["field"]
    assert field not in SCHEMA, (
        f"the schema now closes {field}, so {cls} is no longer advisory. "
        f"Move it to PAIRS and check the values match.")


@pytest.mark.parametrize("entry", sorted(UNPUBLISHED) + sorted(ADVISORY))
def test_every_exception_says_why_and_where_it_ends(entry):
    d = UNPUBLISHED.get(entry) or ADVISORY[entry]
    assert d.get("why"), f"{entry} is excepted without a reason"
    assert d.get("resolve_in"), f"{entry} is excepted with no version to resolve it"
