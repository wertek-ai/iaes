#!/usr/bin/env python3
"""A citation to a section of this standard must point at a section that exists.

Text can be right and its evidence missing. On 2026-09-06 three places in this
repository cited a subsection that has never existed:

    CONTRIBUTING.md              GOVERNANCE.md §1.2
    surface.json                 GOVERNANCE.md section 1.2
    tests/test_release_separation.py   RFC-000 §4.2

Both are numbered *items* inside §1 and §4, not subsections. The second form is
worse than a typo: a real §1.1 sits directly above it, so a reader looks for
§1.2, finds a plausible neighbour, and concludes the document moved.

The mistake is mechanical -- turning "section N, item M" into "§N.M" -- which
is why a mechanical check is the right shape for it.

Deliberately narrow. It checks one thing: that an explicit citation to a
section of an IAES document resolves to a heading that exists. It does not
validate ISO references, IETF RFCs, URLs, bibliography, or whether the cited
section says what the citing text claims. Those are different problems and a
guard that tried to solve them all would be switched off.

Two limits, stated rather than discovered:

  - A citation without a marker -- "GOVERNANCE.md 4.2" with no section sign --
    is not checked. Requiring the marker keeps the false-positive rate at zero,
    and a guard that cries wolf gets disabled.
  - A bare `RFC-NNN` counts as ours only when `rfc/IAES-RFC-NNN.md` exists, so
    that IETF references like RFC-9113 are left alone.

SPDX-License-Identifier: CC-BY-4.0
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__", ".pytest_cache", "coverage"}
SCAN_SUFFIXES = {".md", ".json", ".py", ".ts", ".js", ".yaml", ".yml"}

# The documents whose sections may be cited, by every name they are cited under.
def known_documents() -> dict:
    docs = {
        "GOVERNANCE.md": ROOT / "GOVERNANCE.md",
        "IAES_SPEC.md": ROOT / "IAES_SPEC.md",
        "SDK_SURFACE.md": ROOT / "SDK_SURFACE.md",
    }
    for path in sorted((ROOT / "rfc").glob("IAES-RFC-*.md")):
        number = path.stem.split("-")[-1]          # IAES-RFC-002 -> 002
        docs[f"rfc/{path.name}"] = path
        docs[path.stem] = path                     # IAES-RFC-002
        docs[f"RFC-{number}"] = path               # RFC-002, ours only because
                                                   # the file exists
    return {k: v for k, v in docs.items() if v.exists()}


DOCS = known_documents()

# A section number as this repository writes them: 1, 4.2, 3.2.4, 3-bis.
NUMBER = r"[0-9]+(?:-bis)?(?:\.[0-9]+)*"

# `GOVERNANCE.md` §4.2 · GOVERNANCE.md) §1 · RFC-000 §4, item 2 ·
# SDK_SURFACE.md section 3. A marker is required; see the limits above.
CITATION = re.compile(
    r"(?P<doc>" + "|".join(re.escape(name) for name in sorted(DOCS, key=len, reverse=True)) + r")"
    r"[`)\]]{0,2}\s*"
    r"(?:§|[Ss]ection\s+)\s*"
    r"(?P<number>" + NUMBER + r")"
)

HEADING = re.compile(r"^#+\s+(" + NUMBER + r")\.?(?:\s|$)")


def sections_of(path: Path) -> set:
    found = set()
    for line in path.read_text(encoding="utf-8", errors="replace").split("\n"):
        m = HEADING.match(line)
        if m:
            found.add(m.group(1))
    return found


SECTIONS = {name: sections_of(path) for name, path in DOCS.items()}


def files_to_scan():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        # This file necessarily contains the broken citations it describes.
        if path.name in {"check_citations.py", "test_citations.py"}:
            continue
        yield path


def scan() -> list:
    problems = []
    for path in files_to_scan():
        text = path.read_text(encoding="utf-8", errors="replace")
        # Scanned whole, not line by line. Markdown wraps, so a citation whose
        # document name ends one line and whose number begins the next was
        # invisible to this check -- and the pattern always allowed it, since
        # `\s*` matches a newline. Measured when the gap was found: 2 of 104
        # citations in this repository had never been checked, one of them in
        # an accepted RFC. Both happened to be valid, which is luck, not a
        # result. The line number is derived from the match offset, because a
        # number that points at the wrong line is worse than none.
        for m in CITATION.finditer(text):
            doc, number = m.group("doc"), m.group("number")
            if number in SECTIONS[doc]:
                continue
            n = text.count("\n", 0, m.start()) + 1
            parent = number.rsplit(".", 1)[0] if "." in number else None
            hint = ""
            if parent and parent in SECTIONS[doc]:
                hint = (f" §{parent} exists; if you meant a numbered item "
                        f"inside it, write \"§{parent}, item N\".")
            problems.append((path.relative_to(ROOT).as_posix(), n, doc, number, hint))
    return problems


def main() -> None:
    if not DOCS:
        print("error: no citable documents found", file=sys.stderr)
        raise SystemExit(1)

    problems = scan()
    if not problems:
        total = sum(len(s) for s in SECTIONS.values())
        print(f"every section citation resolves ({len(DOCS)} citable documents, "
              f"{total} sections)")
        print("not checked: ISO and IETF references, URLs, bibliography, and "
              "whether a section says what the citing text claims")
        return

    for rel, n, doc, number, hint in problems:
        print(f"error: {rel}:{n} cites {doc} §{number}, which does not exist.{hint}",
              file=sys.stderr)
    print(f"\n{len(problems)} citation(s) pointing at nothing", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
