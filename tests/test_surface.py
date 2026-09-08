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
REPORT = json.loads((ROOT / "implementations.json").read_text(encoding="utf-8"))
IMPLS = REPORT["implementations"]
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
    # The CANONICAL name, not whichever name happens to work. surface.json
    # requires from_object; from_dict is a deprecated alias, and a detector
    # that accepted either would let an SDK claim the profile while exposing
    # only the old verb -- which is the drift the profile exists to end.
    # Defined on the models AND reachable from the package root. Either alone
    # is not the capability: a classmethod nobody can import is not there for
    # the caller, and surface.json says so in its own words -- Python once had
    # schema_uri_for without exporting it, and that was fixed rather than
    # declared. An earlier version of this check accepted either, so removing
    # from_object from __init__ left it green.
    on_models = all(hasattr(getattr(models, b), "from_object") for b in builders)
    if on_models and hasattr(iaes, "from_object"):
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


def typescript_root_exports() -> set[str]:
    """What `import { x } from "@iaes/sdk"` actually reaches.

    surface.json's own rule: a capability that exists but cannot be reached
    idiomatically does not count. Until 2026-09-08 this file grepped every
    file under npm/src for the definition, so a function that was never
    re-exported from index.ts counted anyway -- the same defect the rule was
    written about, one language over.
    """
    index = (ROOT / "npm" / "src" / "index.ts").read_text(encoding="utf-8")
    names: set[str] = set()
    for block in re.findall(r"export\s*\{([^}]*)\}", index):
        for part in block.split(","):
            name = part.split(" as ")[-1].strip()
            if name and not name.startswith("type "):
                names.add(name)
    return names


def typescript_surface() -> set[str]:
    src = " ".join(p.read_text(encoding="utf-8")
                   for p in (ROOT / "npm" / "src").glob("*.ts"))
    exported = typescript_root_exports()
    found = set()
    # Event builders live in models.ts; client.ts holds the client and its error.
    models = (ROOT / "npm" / "src" / "models.ts").read_text(encoding="utf-8")
    classes = set(re.findall(r"export class (\w+)", models))
    found.add(f"build:{len(classes)}")
    # The canonical name, reachable from the package root -- see the note in
    # python_surface(). `fromJSON` remains as a deprecated alias and does not
    # satisfy the profile on its own.
    if "fromObject" in src and "fromObject" in exported:
        found.add("from_object")
    # Defined AND reachable from the package root. Defining it is not enough:
    # a caller writes `import { validate } from "@iaes/sdk"`, and a function
    # that index.ts never re-exports is not there as far as they are concerned.
    if re.search(r"export function validate\w*\(", src) and "validate" in exported:
        found.add("validate")
    if "computeContentHash" in src and "computeContentHash" in exported:
        found.add("compute_content_hash")
    if "schemaUriFor" in src and "schemaUriFor" in exported:
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


# ─── the profile is only real if a claim can be checked ──────

REQUIRED = [name for name, cap in SURFACE["capabilities"].items() if cap.get("required")]

COUNTED = {"build": PUBLISHED_TYPES, "vocabulary": ENUM_COUNT}


def _offers(impl: dict, capability: str) -> bool:
    """`has` entries are either "name" or "name:count"."""
    for entry in impl.get("has", []):
        name, _, count = entry.partition(":")
        if name != capability:
            continue
        needed = COUNTED.get(capability)
        return True if needed is None else count.isdigit() and int(count) >= needed
    return False


@pytest.mark.parametrize("name", sorted(k for k in IMPLS if not k.startswith("$")))
def test_a_claim_of_the_profile_is_backed_by_every_required_capability(name):
    """Adopting a profile that nothing checks would make it decorative.

    `claims_profile` is true, false, or null for an implementation the profile
    does not apply to. Where it is true, every capability the profile requires
    must actually be offered -- with the full count, since `build: 3` is not
    `build`.
    """
    impl = IMPLS[name]
    if impl.get("claims_profile") is not True:
        pytest.skip(f"{name} does not claim the profile")
    missing = [c for c in REQUIRED if not _offers(impl, c)]
    assert not missing, (
        f"{name} claims the IAES SDK profile and does not offer {missing}. "
        f"Either the capability lands or the claim comes down."
    )


def test_every_implementation_says_whether_it_claims_the_profile():
    """Silence would read as 'not applicable' for a library that simply has
    not been assessed."""
    for name, impl in IMPLS.items():
        if name.startswith("$"):
            continue
        assert "claims_profile" in impl, f"{name} does not say whether it claims the profile"
        assert impl.get("claim_note"), f"{name} claims nothing and gives no reason"


def test_the_measurement_only_names_capabilities_the_profile_defines():
    """The two files split on 2026-09-08 and can now drift apart.

    A measurement that reports on a capability the profile does not define is
    measuring something nobody asked for; one that silently renames a
    capability makes the claim guard test a name that does not exist. Neither
    fails on its own, which is why it is checked here.
    """
    defined = set(SURFACE["capabilities"])
    for name, impl in IMPLS.items():
        if name.startswith("$"):
            continue
        for entry in list(impl.get("has", [])) + list(impl.get("gaps", [])):
            capability = entry.partition(":")[0].strip()
            assert capability in defined, (
                f"{name} reports on {capability!r}, which surface.json does not "
                f"define. Either the profile gained it or the report is stale."
            )


def test_the_profile_carries_no_implementation_status():
    """surface.json is normative. If an SDK release could edit it, a package
    shipping would be a change to the standard."""
    for key in ("implementations", "claims_profile", "measured"):
        assert key not in SURFACE, (
            f"surface.json carries {key!r}. The definition of the profile must "
            f"not record who currently meets it: that belongs in "
            f"implementations.json, which is not normative."
        )


# ─── the deprecated aliases have to keep working ─────────────

def test_the_python_alias_still_works_and_says_it_is_deprecated():
    """Renaming without keeping the old name would break every caller and make
    a naming decision into a MAJOR change (rfc/IAES-RFC-006.md §4)."""
    import warnings

    import iaes

    event = {
        "spec_version": "2.0", "event_type": "asset.health",
        "event_id": "x", "correlation_id": "x",
        "timestamp": "2026-09-08T12:00:00Z", "source": "acme.d",
        "asset": {"asset_id": "M1"},
        "data": {"health_index": 0.5, "severity": "medium"},
    }

    canonical = iaes.from_object(event)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        alias = iaes.from_dict(event)
        assert any(issubclass(w.category, DeprecationWarning) for w in caught), (
            "the alias works and never says it is deprecated, so nobody moves"
        )
    assert type(alias) is type(canonical)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        on_class = iaes.AssetHealth.from_dict(event)
        assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert type(on_class) is type(canonical)


def test_the_typescript_alias_is_declared_deprecated_rather_than_deleted():
    """TypeScript has no quiet runtime deprecation channel, so the marker is
    `@deprecated`, which an editor and a type-checker already act on. What is
    checked here is that the alias exists and is marked -- deleting it would be
    the MAJOR change §4 avoids, and keeping it unmarked would say nothing."""
    models = (ROOT / "npm" / "src" / "models.ts").read_text(encoding="utf-8")
    assert "export function fromJSON" in models, "the alias was deleted"
    assert re.search("@deprecated" + chr(46) + "*fromObject", models), (
        "the alias exists and is not marked deprecated, so nobody moves"
    )
    index = (ROOT / "npm" / "src" / "index.ts").read_text(encoding="utf-8")
    assert "fromJSON" in index and "fromObject" in index, (
        "both names must be reachable: the canonical one to satisfy the "
        "profile, the alias so existing callers keep working"
    )
