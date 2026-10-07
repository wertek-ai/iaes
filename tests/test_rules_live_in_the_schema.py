"""A rule of IAES is written once, in schema/, and everyone is made to read it there.

The implementations take the shape rules -- published types, schema files,
required data fields, closed catalogues -- from the files
tools/generate_from_schema.py writes, or read the schemas at run time. These
tests make that the only way:

1. the generated files are what the generator writes from today's schemas;
2. no other implementation file carries a complete copy of a closed catalogue
   or of the list of published types, written by hand.

The second is what was missing. tests/test_catalogs.py held the two SDKs to the
schemas; nothing held the n8n Emit form, and on 2026-10-06 it lacked `unknown`
(iso_13374_status) and `alert` (triggered_by). A copy that a test compares is
still a copy someone has to remember to update; a copy that is not allowed
cannot drift.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GENERATED = {
    "src/iaes/_from_schema.py", "src/iaes/enums.py",
    "npm/src/fromSchema.ts", "npm/src/enums.ts",
}

#: Implementation sources a copy could hide in.
SOURCES = sorted(
    [p for p in (ROOT / "src" / "iaes").glob("*.py")]
    + [p for p in (ROOT / "npm" / "src").glob("*.ts")]
    + [p for p in (ROOT / "node-red" / "nodes").glob("*.js")]
    + [p for p in (ROOT / "n8n-nodes" / "nodes").rglob("*.ts")]
)

#: Files allowed to name every published type, with the reason. A binding from
#: a type to the class that builds it is not a copy of the list: it is the one
#: thing the schema cannot say, and tests/test_published_types_are_one_list.py
#: holds it to schema/.
MAY_NAME_EVERY_TYPE = {
    "src/iaes/models.py": "EVENT_TYPES binds each published type to its model class",
    "npm/src/models.ts": "EVENT_TYPES binds each published type to its model class",
    "node-red/nodes/iaes-route.js": (
        "EVENT_TYPES is ORDERED: the position of a type is the output it leaves by, and deployed "
        "flows are wired to those positions. Generating it (in any other order) would rewire "
        "users' flows silently. test_published_types_are_one_list.py holds its membership to "
        "schema/; a new published type needs a decision on its output, not a regenerated list."
    ),
}

LITERAL = re.compile(r"""["']([a-z][a-z0-9_.]*)["']""")


def schemas():
    out = {}
    for path in sorted((ROOT / "schema").glob("*.schema.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        t = doc["$id"].rsplit("/", 1)[-1]
        if t != "envelope":
            out[t] = doc
    return out


def closed_catalogues():
    found = {}
    for t, doc in schemas().items():
        for field, spec in doc.get("properties", {}).get("data", {}).get("properties", {}).items():
            if "enum" in spec:
                found[f"{t} data.{field}"] = {v for v in spec["enum"] if v is not None}
    return found


def rel(path):
    return path.relative_to(ROOT).as_posix()


def test_the_generated_files_are_fresh():
    out = subprocess.run([sys.executable, "tools/generate_from_schema.py", "--check"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr


def test_the_sources_were_found():
    # Control: if the globs stopped matching, the tests below would pass on nothing.
    names = {rel(p) for p in SOURCES}
    assert "n8n-nodes/nodes/IaesEmit/IaesEmit.node.ts" in names
    assert "node-red/nodes/iaes-validate.js" in names
    assert GENERATED <= names


def test_no_implementation_copies_a_closed_catalogue():
    catalogues = closed_catalogues()
    assert len(catalogues) >= 10, "the schemas' closed catalogues were not found"
    copies = []
    for path in SOURCES:
        if rel(path) in GENERATED:
            continue
        literals = set(LITERAL.findall(path.read_text(encoding="utf-8")))
        for name, values in catalogues.items():
            # A catalogue of one or two common words ("low", "high") would match
            # by accident; every IAES catalogue has three values or more.
            if len(values) >= 3 and values <= literals:
                copies.append(f"{rel(path)} copies {name}")
    assert not copies, (
        "closed catalogues written by hand outside the generated files; take them from "
        "CATALOGS or the SDK's enumerations instead:\n  " + "\n  ".join(copies))


def test_no_implementation_copies_the_published_types():
    published = set(schemas())
    copies = []
    for path in SOURCES:
        if rel(path) in GENERATED or rel(path) in MAY_NAME_EVERY_TYPE:
            continue
        if published <= set(LITERAL.findall(path.read_text(encoding="utf-8"))):
            copies.append(rel(path))
    assert not copies, (
        "the list of published types written by hand; use PUBLISHED_EVENT_TYPES:\n  "
        + "\n  ".join(copies))


def test_the_guard_sees_a_copy_when_there_is_one():
    """Control: the literal match finds a catalogue written out in full."""
    text = "const x = ['info', 'low', 'medium', 'high', 'critical'];"
    literals = set(LITERAL.findall(text))
    assert closed_catalogues()["asset.health data.severity"] <= literals
