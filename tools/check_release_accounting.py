#!/usr/bin/env python3
"""No normative change enters a release without an Accepted decision explaining it.

The release manifest answers *what changed*. It cannot answer *who decided it*,
and that second question is the one a release gate has to close: a normative
diff with no memo behind it is a change to the standard that nobody approved.

Three times in the work leading to 2.0 a careful human inventory came back
incomplete — three schema strings that turned out to be eight changes, an ISO
8601 narrowing filed as a citation fix, and a migration statement that
contradicted a memo travelling in the same release. None of those was
carelessness; all three were a person reading a diff. So this is mechanical.

    python tools/check_release_accounting.py --base spec-v1.4 --head HEAD

The ledger it reads is **release engineering, not normative**. It carries no
meaning: the artifacts carry that, and the RFCs carry the rationale. It answers
one question only — *do we have an explanation for every modification we are
about to publish?*

SPDX-License-Identifier: CC-BY-4.0
"""

import argparse
import fnmatch
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_manifest_tool():
    """The normative set is defined in one place, and this is not it."""
    spec = importlib.util.spec_from_file_location(
        "iaes_release_manifest", ROOT / "tools" / "build_release_manifest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MANIFEST = _load_manifest_tool()


def digest_at(ref: str, path: str) -> str | None:
    """The content of a file at a ref, or None if it is not there."""
    out = subprocess.run(["git", "show", f"{ref}:{path}"],
                         cwd=ROOT, capture_output=True)
    if out.returncode != 0:
        return None
    return hashlib.sha256(out.stdout).hexdigest()


def normative_paths(ref: str) -> set:
    return {str(p.relative_to(MANIFEST.ROOT)).replace("\\", "/")
            for p in MANIFEST.normative_files(ref)}


def change_set(base: str, head: str) -> dict:
    """Every normative path that differs between the two refs, and how."""
    before, after = normative_paths(base), normative_paths(head)
    changes = {}
    for path in sorted(before | after):
        if path not in before:
            changes[path] = "added"
        elif path not in after:
            changes[path] = "removed"
        elif digest_at(base, path) != digest_at(head, path):
            changes[path] = "modified"
    return changes


def rfc_state(number: str) -> tuple:
    """(state, path) for an RFC, read from the memo itself."""
    path = ROOT / "rfc" / f"IAES-RFC-{number}.md"
    if not path.exists():
        return None, path
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\*\*State:\s*(\w+)\*\*", text)
    return (match.group(1) if match else None), path


def uncommitted_normative_paths() -> list:
    """Normative-looking paths that differ in the working tree.

    This tool reads refs, which is right: a release is made of committed
    content, and the manifest says so. But that makes a specific false PASS
    possible, and it caught the author while arming the decoys -- a brand new
    schema, uncommitted, is invisible to `git ls-tree`, so the gate reported
    zero orphans over a file that would have shipped.

    Reading the working tree instead would be worse: it would let the gate pass
    on content no tag can carry. So the refs stay authoritative and this refuses
    to answer while the answer could be stale.
    """
    out = subprocess.run(["git", "status", "--porcelain", "--"] + MANIFEST.NORMATIVE
                         + MANIFEST.NORMATIVE_GLOBS,
                         cwd=ROOT, capture_output=True, text=True).stdout
    return [line[3:] for line in out.splitlines() if line.strip()]


def check(ledger_path: Path, base: str, head: str) -> int:
    dirty = uncommitted_normative_paths()
    if dirty and head == "HEAD":
        print("normative files differ from HEAD in the working tree:",
              file=sys.stderr)
        for path in dirty:
            print(f"  - {path}", file=sys.stderr)
        print("",  file=sys.stderr)
        print("This gate reads committed content, because that is what a "
              "tag can carry. Commit or revert these before asking it.",
              file=sys.stderr)
        return 1

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if ledger.get("base") != base:
        print(f"the ledger accounts for {ledger.get('base')!r}, not {base!r}",
              file=sys.stderr)
        return 1

    changes = change_set(base, head)
    problems = []

    # Every cited memo exists and has been Accepted. A rationale still under
    # consideration is not an explanation: GOVERNANCE.md §6 says Accepted means
    # the change has been incorporated, which is exactly what is being checked.
    covered: dict = {}
    for number, patterns in sorted(ledger["rfc"].items()):
        state, path = rfc_state(number)
        if state is None:
            problems.append(f"the ledger cites RFC-{number}, and {path.name} "
                            f"does not exist or declares no State")
            continue
        if state != "Accepted":
            problems.append(f"RFC-{number} is {state}, not Accepted. A release "
                            f"may not carry a change whose decision is still "
                            f"under consideration.")
        matched_any = False
        for pattern in patterns:
            hits = [p for p in changes if fnmatch.fnmatch(p, pattern)]
            if not hits:
                problems.append(
                    f"RFC-{number} accounts for {pattern!r}, which does not "
                    f"change between {base} and {head}. Stale accounting: "
                    f"remove the entry or restore the change.")
            for hit in hits:
                covered.setdefault(hit, []).append(number)
                matched_any = True
        if not matched_any and patterns:
            problems.append(f"RFC-{number} accounts for nothing that changed")

    for path, how in sorted(changes.items()):
        if path not in covered:
            problems.append(
                f"{path} is {how} and no RFC accounts for it. A normative "
                f"change with no decision behind it is a change to the "
                f"standard that nobody approved.")

    print(f"IAES {ledger['target']} normative accounting\n")
    for number in sorted(ledger["rfc"]):
        state, _ = rfc_state(number)
        mine = sorted(p for p, r in covered.items() if number in r)
        mark = "covered" if mine and state == "Accepted" else "PROBLEM"
        print(f"  RFC-{number}   {mark:8} {state or '?':9} {len(mine)} file(s)")

    orphans = [p for p in changes if p not in covered]
    unaccepted = [n for n in ledger["rfc"] if rfc_state(n)[0] != "Accepted"]
    stale = [m for m in problems if "Stale accounting" in m]
    print(f"\n  normative files changed:   {len(changes)}")
    print(f"  orphan normative changes:  {len(orphans)}")
    print(f"  unaccepted rationale:      {len(unaccepted)}")
    print(f"  stale accounting entries:  {len(stale)}")

    if problems:
        print("\nFAIL\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print("\nPASS")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True, help="the published release tag")
    ap.add_argument("--head", default="HEAD", help="the release candidate")
    ap.add_argument("--ledger", type=Path,
                    default=ROOT / "release" / "accounting-2.0.json")
    args = ap.parse_args()
    raise SystemExit(check(args.ledger, args.base, args.head))


if __name__ == "__main__":
    main()
