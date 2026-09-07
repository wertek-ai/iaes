#!/usr/bin/env python3
"""Every external document this specification cites is identified and its
availability declared.

Second rung of three, and it answers only its own question:

    citation exists      does the thing I point at exist?      check_citations.py
    document available   is it the document I say, and can      this file
                         anyone consult it?
    relation valid       does it support what I attribute       not built
                         to it?

Keeping them apart is the point. When CI goes red you should know immediately
whether you have a broken reference, an undeclared document, or an unsupported
claim -- a single check that answered "something is wrong" would answer almost
nothing.

So this deliberately does NOT check whether a cited document says what the
specification claims. That is the third rung, and it needs the documents open.

Stdlib only, like its neighbours: it must run and fail before any toolchain
installs.

SPDX-License-Identifier: CC-BY-4.0
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "references" / "registry.json"
SPEC = ROOT / "IAES_SPEC.md"

# Fields each availability value obliges. An entry that claims a copy must say
# which copy, because an edition is part of the evidence's identity.
REQUIRED_BY_AVAILABILITY = {
    "public": (),
    "available": ("edition", "language", "access_basis"),
    "unavailable": (),
    "unresolved": ("note",),
}

# A standard published in parts. Citing one without a part names no document.
MULTIPART = {"13374", "81346", "13849", "61508", "62443"}


def load_registry() -> dict:
    """Rejects duplicate keys rather than silently keeping the last."""
    def no_duplicates(pairs):
        seen = {}
        for k, v in pairs:
            if k in seen:
                raise SystemExit(
                    f"error: references/registry.json defines {k!r} twice. "
                    f"JSON parsers keep the last one silently, so two truths "
                    f"become one without anybody choosing which.")
            seen[k] = v
        return seen

    if not REGISTRY.exists():
        raise SystemExit(f"error: {REGISTRY.relative_to(ROOT)} is missing. Every "
                         f"external document the specification cites is declared there.")
    return json.loads(REGISTRY.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)


def cited_documents() -> list:
    """The external documents named in the specification's References section."""
    text = SPEC.read_text(encoding="utf-8")
    start = text.index("## References")
    end = text.index("## Appendix A", start)
    section = text[start:end]

    found = []
    for line in section.split("\n"):
        if not line.startswith("|"):
            continue
        cell = line.split("|")[1].strip()
        # A cell may name more than one, as "RFC 2119, RFC 8174".
        for m in re.finditer(r"\b(RFC|ISO|IEC)\s+([0-9]+(?:-[0-9]+)?)(\s+series)?", cell):
            publisher, number, series = m.group(1), m.group(2), bool(m.group(3))
            found.append((f"{publisher} {number}" + (" series" if series else ""),
                          publisher, number, series))
    return found


def main() -> None:
    registry = load_registry()
    entries = registry.get("references", [])
    by_citation = {e.get("cited_as"): e for e in entries}
    problems = []

    # 1. Everything the specification cites is declared.
    for cited_as, publisher, number, series in cited_documents():
        # Asked first, deliberately. A multi-part standard cited without a part
        # names no document, so "it is not in the registry" would be true and
        # would teach the wrong repair: adding a registry entry for a family.
        if publisher == "ISO" and number in MULTIPART and "-" not in number and not series:
            problems.append(
                f"{cited_as} is a multi-part standard and does not identify a "
                f"document. Cite a part and edition, or write "
                f"\"{publisher} {number} series\" if the statement concerns the "
                f"family as a whole. Do not add a registry entry for it: "
                f"availability cannot be answered about a family.")
            continue

        entry = by_citation.get(cited_as)
        if entry is None:
            problems.append(
                f"IAES_SPEC.md cites {cited_as}, which references/registry.json does "
                f"not declare. Add an entry with its `cited_as`, its identity and its "
                f"availability, so a reader can tell whether the claim can be checked.")
            continue

        # 2. Each entry says enough for its own availability value.
        av = entry.get("availability")
        if av not in REQUIRED_BY_AVAILABILITY:
            problems.append(
                f"{entry.get('id')}: availability {av!r} is not one of "
                f"{sorted(REQUIRED_BY_AVAILABILITY)}.")
            continue
        for field in REQUIRED_BY_AVAILABILITY[av]:
            if not entry.get(field):
                problems.append(
                    f"{entry.get('id')}: availability is {av!r} and `{field}` is "
                    f"missing. A held copy is a specific edition in a specific "
                    f"language; without them the entry names a family, not evidence.")

    # 3. Nothing declared that nothing cites.
    cited_names = {c for c, _, _, _ in cited_documents()}
    for entry in entries:
        if entry.get("cited_as") not in cited_names:
            problems.append(
                f"{entry.get('id')}: declared in the registry and cited nowhere in "
                f"IAES_SPEC.md. Remove it, or cite it. A registry that outlives its "
                f"citations stops describing the specification.")

    if problems:
        for p in problems:
            print("error: " + p, file=sys.stderr)
        print(f"\n{len(problems)} problem(s) in the reference registry", file=sys.stderr)
        raise SystemExit(1)

    counts = {}
    for e in entries:
        counts[e["availability"]] = counts.get(e["availability"], 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
    print(f"every cited document is declared and its availability stated ({summary})")
    print("not checked here: whether a document supports what the specification "
          "attributes to it -- that needs the document open, and is a separate question")


if __name__ == "__main__":
    main()
