#!/usr/bin/env python3
"""Enforce the IAES compatibility policy on every schema change.

GOVERNANCE.md §4 declares BACKWARD compatibility as the default mode: a consumer
built for version N must be able to read events produced against N-1. That is a
promise to implementers, and a promise nobody checks is a wish. This is the
check.

It compares the schemas in the working tree against a baseline (by default the
schemas as published on the last release) and fails when it finds a change that
§4.2 classifies as MAJOR. It does not judge intent: a MAJOR change is legitimate,
it just cannot ship as a MINOR release. To ship one, bump the major version and
pass --allow-major.

    python tools/check_schema_compat.py --baseline <git-ref>
    python tools/check_schema_compat.py --baseline HEAD~1 --allow-major

Exit codes: 0 compatible, 1 breaking change found, 2 usage or IO error.

Deliberately written without dependencies: it has to run in CI before anything
is installed, and a guard that needs a toolchain is a guard that gets skipped.
"""

import argparse
import json
import os
import re
import subprocess
import sys

SCHEMA_DIR = "schema"


# --------------------------------------------------------------------------- #
# Reading the baseline
# --------------------------------------------------------------------------- #

def read_at_ref(ref, path):
    """File content at a git ref, or None if it did not exist there."""
    try:
        out = subprocess.run(
            ["git", "show", "%s:%s" % (ref, path)],
            capture_output=True, check=True,
        )
        return json.loads(out.stdout.decode("utf-8"))
    except subprocess.CalledProcessError:
        return None
    except json.JSONDecodeError as e:
        fail_hard("baseline %s:%s is not valid JSON (%s)" % (ref, path, e))


def fail_hard(msg):
    print("ERROR: %s" % msg, file=sys.stderr)
    sys.exit(2)


# --------------------------------------------------------------------------- #
# The checks. One function per rule in GOVERNANCE.md §4.2.
# --------------------------------------------------------------------------- #

def walk(old, new, path, breaks):
    """Recursively compare two schema fragments and collect breaking changes."""
    if not isinstance(old, dict) or not isinstance(new, dict):
        return

    here = path or "(root)"

    # §4.2 — Changing the canonical $id of a schema.
    # The §5.1 exception (an identity that never resolved) is deliberately NOT
    # automated: it requires evidence that the old URI never resolved, and that
    # judgement belongs to a human, recorded in the version history.
    if old.get("$id") and new.get("$id") and old["$id"] != new["$id"]:
        breaks.append((
            here,
            "canonical $id changed",
            "%s -> %s" % (old["$id"], new["$id"]),
            "MAJOR, unless GOVERNANCE.md 5.1 applies (identity that never "
            "resolved) — that exception is claimed by hand, in the version history",
        ))

    # §4.2 — Making an optional field required.
    old_req = set(old.get("required") or [])
    new_req = set(new.get("required") or [])
    for field in sorted(new_req - old_req):
        breaks.append((
            here, "field became required", field,
            "a producer that omitted it now fails validation",
        ))

    # §4.2 — Removing or renaming a field.
    old_props = old.get("properties") or {}
    new_props = new.get("properties") or {}
    for field in sorted(set(old_props) - set(new_props)):
        breaks.append((
            here, "field removed", field,
            "a consumer reading it now finds nothing; a rename looks identical "
            "to a removal from the outside",
        ))

    for field in sorted(set(old_props) & set(new_props)):
        o, n = old_props[field], new_props[field]
        if isinstance(o, dict) and isinstance(n, dict):
            check_property(o, n, "%s.%s" % (here, field), breaks)
            walk(o, n, "%s.%s" % (here, field), breaks)

    # Nested subschemas that are not properties.
    for key in ("items", "additionalProperties", "$defs", "definitions"):
        o, n = old.get(key), new.get(key)
        if isinstance(o, dict) and isinstance(n, dict):
            if key in ("$defs", "definitions"):
                for name in sorted(set(o) & set(n)):
                    if isinstance(o[name], dict) and isinstance(n[name], dict):
                        walk(o[name], n[name], "%s.%s.%s" % (here, key, name), breaks)
                for name in sorted(set(o) - set(n)):
                    breaks.append((
                        here, "definition removed", "%s.%s" % (key, name),
                        "anything that referenced it can no longer resolve",
                    ))
            else:
                walk(o, n, "%s.%s" % (here, key), breaks)


def check_property(old, new, where, breaks):
    """§4.2 — Narrowing a constraint on a single property."""

    # An open string closed into an enumeration, or an enumeration losing values.
    old_enum, new_enum = old.get("enum"), new.get("enum")
    if new_enum is not None and old_enum is None:
        breaks.append((
            where, "closed into an enumeration", "%d allowed values" % len(new_enum),
            "every value outside the list stops validating — this is the "
            "'unit' case worked through in GOVERNANCE.md 4.2",
        ))
    elif old_enum is not None and new_enum is not None:
        gone = [v for v in old_enum if v not in new_enum]
        if gone:
            breaks.append((
                where, "enumeration values removed", ", ".join(map(str, gone[:6])),
                "producers still sending them now fail",
            ))

    # A pattern added, or replaced by a different one.
    if new.get("pattern") and not old.get("pattern"):
        # Adding a pattern normally narrows. There is one case where it does
        # not: a field that used to be a closed enumeration and is being opened
        # into a shape. Then the question is not "was a pattern added?" but
        # "does everything that used to validate still validate?" — and that is
        # measurable, so it gets measured instead of assumed.
        opened = old_enum is not None and new_enum is None
        still_valid = opened and all(
            isinstance(v, str) and re.match(new["pattern"], v) for v in old_enum
        )
        if not still_valid:
            breaks.append((
                where, "pattern added", new["pattern"],
                "strings that used to be free now have to match"
                + ("; and not every value of the enumeration it replaces matches it"
                   if opened else ""),
            ))
    elif old.get("pattern") and new.get("pattern") and old["pattern"] != new["pattern"]:
        breaks.append((
            where, "pattern changed", "%s -> %s" % (old["pattern"], new["pattern"]),
            "cannot be assumed wider; treat as narrowing unless proven otherwise",
        ))

    # A numeric or length range tightened.
    for key, tighter in (
        ("minimum", lambda o, n: n > o), ("maximum", lambda o, n: n < o),
        ("minLength", lambda o, n: n > o), ("maxLength", lambda o, n: n < o),
        ("minItems", lambda o, n: n > o), ("maxItems", lambda o, n: n < o),
    ):
        o, n = old.get(key), new.get(key)
        if n is not None and (o is None or tighter(o, n)):
            breaks.append((
                where, "%s tightened" % key, "%s -> %s" % (o, n),
                "values that used to pass now fail",
            ))

    # A type narrowed. ["string","null"] -> "string" drops null.
    def as_set(t):
        if t is None:
            return None
        return set(t) if isinstance(t, list) else {t}

    o_t, n_t = as_set(old.get("type")), as_set(new.get("type"))
    if o_t and n_t and (o_t - n_t):
        breaks.append((
            where, "type narrowed", "%s -> %s" % (sorted(o_t), sorted(n_t)),
            "dropping a type rejects payloads that were valid",
        ))

    # additionalProperties going from allowed to forbidden.
    if old.get("additionalProperties") is not False and new.get("additionalProperties") is False:
        breaks.append((
            where, "additionalProperties closed", "true/absent -> false",
            "any extra field a producer sends now fails; this also defeats the "
            "extensibility the specification promises",
        ))


# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", required=True,
                    help="git ref to compare against (e.g. a release tag, or HEAD~1)")
    ap.add_argument("--allow-major", action="store_true",
                    help="the release is a MAJOR bump; report findings but do not fail")
    args = ap.parse_args()

    if not os.path.isdir(SCHEMA_DIR):
        fail_hard("run this from the repository root (no ./%s)" % SCHEMA_DIR)

    files = sorted(f for f in os.listdir(SCHEMA_DIR) if f.endswith(".schema.json"))
    if not files:
        fail_hard("no schemas found in ./%s" % SCHEMA_DIR)

    breaks, checked, added = [], 0, []
    for name in files:
        path = os.path.join(SCHEMA_DIR, name).replace(os.sep, "/")
        old = read_at_ref(args.baseline, path)
        if old is None:
            added.append(name)          # a new schema breaks nobody
            continue
        with open(path, encoding="utf-8") as fh:
            new = json.load(fh)
        checked += 1
        found = []
        walk(old, new, "", found)
        breaks.extend((name,) + b for b in found)

    print("IAES compatibility check — GOVERNANCE.md 4 (mode: BACKWARD)")
    print("  baseline : %s" % args.baseline)
    print("  compared : %d schema(s)" % checked)
    if added:
        print("  new      : %s (adding a schema is MINOR)" % ", ".join(added))

    # A schema present in the baseline and gone from the tree.
    removed = []
    try:
        out = subprocess.run(["git", "ls-tree", "--name-only", "%s:%s" % (args.baseline, SCHEMA_DIR)],
                             capture_output=True, check=True)
        base_files = [f for f in out.stdout.decode().split() if f.endswith(".schema.json")]
        removed = sorted(set(base_files) - set(files))
    except subprocess.CalledProcessError:
        pass
    for name in removed:
        breaks.append((name, "(file)", "schema removed", name,
                       "its $id stops resolving; GOVERNANCE.md 4.3 says nothing is ever unpublished"))

    if not breaks:
        print("\nOK — no breaking change. This can ship as MINOR or PATCH.")
        return 0

    print("\n%d breaking change(s) found:\n" % len(breaks))
    for b in breaks:
        schema, where, what, detail, why = b
        print("  %s  %s" % (schema, where))
        print("      %s: %s" % (what, detail))
        print("      why it breaks: %s" % why)
        print("")

    if args.allow_major:
        print("--allow-major given: reported, not blocking. Confirm that the")
        print("version history announces the MAJOR bump and the migration.")
        return 0

    print("Blocked. Per GOVERNANCE.md 4.2 these are MAJOR changes.")
    print("Either keep the change backward compatible, or bump the major version,")
    print("announce it in the version history, and re-run with --allow-major.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
