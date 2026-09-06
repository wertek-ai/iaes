"""surface.json says what each implementation offers. This checks it is true.

Until 2026-09-06 that file claimed, in the present tense, that "this file is
what the test suites read". Nothing read it. So its declarations drifted: it
said Python lacked schema_uri_for, which Python has had all along; it said n8n
lacked validation, which ships as a node; and it said C++ exposed seven of
eight enumerations when there are ten.

A declaration nobody checks is worse than no declaration, because it is quoted.

The C++ runtime lives in another repository and is not checked here. That is a
real hole, and surface.json says so rather than leaving it implied.
"""

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

SURFACE = json.loads((ROOT / "surface.json").read_text(encoding="utf-8"))
IMPLS = SURFACE["implementations"]
PUBLISHED_TYPES = SURFACE["capabilities"]["build"]["published_types"]
ENUM_COUNT = SURFACE["capabilities"]["vocabulary"]["count"]


# ─── what is actually there ──────────────────────────────────

def python_surface() -> set[str]:
    import enum
    import inspect

    import iaes
    from iaes import models, validation

    found = set()
    builders = [n for n, o in vars(models).items()
                if inspect.isclass(o) and hasattr(o, "to_dict") and not n.startswith("_")]
    found.add(f"build:{len(builders)}")
    if any(hasattr(getattr(models, b), "from_dict") for b in builders):
        found.add("from_object")
    if callable(getattr(validation, "validate", None)):
        found.add("validate")
    if callable(getattr(iaes, "compute_content_hash", None)):
        found.add("compute_content_hash")
    if callable(getattr(iaes, "schema_uri_for", None)):
        found.add("schema_uri_for")
    enums = [n for n, o in vars(iaes).items()
             if inspect.isclass(o) and issubclass(o, enum.Enum)]
    found.add(f"vocabulary:{len(enums)}")
    return found


def typescript_surface() -> set[str]:
    src = " ".join(p.read_text(encoding="utf-8")
                   for p in (ROOT / "npm" / "src").glob("*.ts"))
    found = set()
    # Event builders live in models.ts; client.ts holds the client and its error.
    models = (ROOT / "npm" / "src" / "models.ts").read_text(encoding="utf-8")
    classes = set(re.findall(r"export class (\w+)", models))
    found.add(f"build:{len(classes)}")
    if "fromJSON" in src:
        found.add("from_object")
    # A validator, not the word: the SDK has no schema checker today.
    if re.search(r"export function validate\w*\(", src):
        found.add("validate")
    if "computeContentHash" in src:
        found.add("compute_content_hash")
    if "schemaUriFor" in src:
        found.add("schema_uri_for")
    # Idiomatic modern TypeScript: a frozen object plus a type of the same
    # name, not `export enum`. Counting the keyword would have reported zero.
    enums_src = (ROOT / "npm" / "src" / "enums.ts").read_text(encoding="utf-8")
    enums = set(re.findall(r"export const (\w+) = \{", enums_src))
    found.add(f"vocabulary:{len(enums)}")
    return found


def node_red_surface() -> set[str]:
    nodes = {p.stem.replace("iaes-", "")
             for p in (ROOT / "node-red" / "nodes").glob("iaes-*.js")}
    found = set()
    builders = nodes - {"publish", "route", "validate", "sparkplug"}
    found.add(f"build:{len(builders)}")
    if "validate" in nodes:
        found.add("validate")
    if "route" in nodes:
        found.add("route")
    # The vocabulary comes from the SDK the package depends on.
    pkg = json.loads((ROOT / "node-red" / "package.json").read_text(encoding="utf-8"))
    if "@iaes/sdk" in pkg.get("dependencies", {}):
        found.add(f"vocabulary:{ENUM_COUNT}")
    return found


def n8n_surface() -> set[str]:
    nodes_dir = ROOT / "n8n-nodes" / "nodes"
    names = {p.name for p in nodes_dir.iterdir() if p.is_dir()}
    found = set()
    emit = " ".join(p.read_text(encoding="utf-8")
                    for p in (nodes_dir / "IaesEmit").rglob("*.ts")) if "IaesEmit" in names else ""
    types = {m for m in re.findall(r"value: '((?:asset|maintenance|sensor)\.[a-z_]+)'", emit)}
    found.add(f"build:{len(types)}")
    if "IaesValidate" in names:
        found.add("validate")
    pkg = json.loads((ROOT / "n8n-nodes" / "package.json").read_text(encoding="utf-8"))
    if "@iaes/sdk" in pkg.get("dependencies", {}):
        found.add(f"vocabulary:{ENUM_COUNT}")
    return found


MEASURED = {
    "python": python_surface,
    "typescript": typescript_surface,
    "node_red": node_red_surface,
    "n8n": n8n_surface,
}


# ─── the declaration must match ──────────────────────────────

@pytest.mark.parametrize("name", sorted(MEASURED))
def test_declared_capabilities_are_present(name):
    declared = set(IMPLS[name]["has"])
    actual = MEASURED[name]()
    missing = declared - actual
    assert not missing, (
        f"surface.json says {name} has {sorted(missing)}, and it does not. "
        f"Measured: {sorted(actual)}")


@pytest.mark.parametrize("name", sorted(MEASURED))
def test_declared_gaps_are_really_absent(name):
    """A gap that has quietly been filled is a lie in the other direction."""
    actual = MEASURED[name]()
    simple = {g for g in IMPLS[name]["gaps"] if ":" not in g}
    filled = simple & {a.split(":")[0] for a in actual}
    assert not filled, (
        f"surface.json declares {sorted(filled)} missing from {name}, but it is "
        f"there. Close the gap in the file, not only in the code.")


def test_every_implementation_is_declared_or_excused(name=None):
    """No implementation may be absent from the file without saying why."""
    for impl, entry in IMPLS.items():
        if impl.startswith("$"):
            continue
        if impl not in MEASURED:
            assert entry.get("repo") != "this", (
                f"{impl} lives in this repository and nothing measures it")
            assert entry.get("note"), (
                f"{impl} is not measured here and gives no reason")


def test_the_counts_come_from_one_place():
    """The published type count and the enum count are declared once."""
    schemas = {p.name for p in (ROOT / "schema").glob("*.schema.json")}
    published = len(schemas) - 1  # the envelope is not an event type
    assert published == PUBLISHED_TYPES, (
        f"surface.json says {PUBLISHED_TYPES} published types; the schema "
        f"directory holds {published}")
    assert f"vocabulary:{ENUM_COUNT}" in python_surface(), (
        f"surface.json says {ENUM_COUNT} enumerations; Python exports a "
        f"different number")
