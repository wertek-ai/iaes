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

One limit, stated rather than discovered. A mention is declared by name, so
declaring one exempts every occurrence of that name -- including a real
dependency added later under the same name. Making it per-occurrence would
mean tracking line numbers, which go stale on every edit and would produce
false failures on reflow. The exemption list is short, each entry carries its
reason, and both are reviewed when it changes; that is the trade, and it is a
trade rather than an oversight.

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

# The artifacts that can make a normative claim, and therefore the artifacts
# whose external references have to be accounted for. Deliberately not a
# curated table inside the specification: checking a declaration against
# another copy of the same declaration proves only that we wrote it twice.
# RFCs are excluded because they are rationale, not authority (GOVERNANCE.md
# 6.1), and SDK_SURFACE.md is excluded until it is settled who grants it the
# authority it claims for itself.
NORMATIVE_ARTIFACTS = ["IAES_SPEC.md", "GOVERNANCE.md"]
NORMATIVE_GLOBS = ["schema/*.schema.json"]

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

# Publishers whose documents are immutable once numbered: a revision gets a new
# number rather than a new edition of the old one. For these a number alone
# identifies a document. ISO revises under the same number, so an ISO citation
# without an edition does not.
IMMUTABLE_PUBLISHERS = {"RFC"}

CITATION = re.compile(
    r"\b(RFC|ISO/TS|ISO/IEC|ISO|IEC)[ /]([0-9]{3,5}(?:-[0-9]+)?)(:[0-9]{4})?(\s+series)?")


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


def normative_files() -> list:
    files = [ROOT / p for p in NORMATIVE_ARTIFACTS]
    for pattern in NORMATIVE_GLOBS:
        files.extend(sorted(ROOT.glob(pattern)))
    missing = [f for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"error: normative artifact missing: {missing}")
    return files


def cited_documents() -> dict:
    """Every external document named by a normative artifact, and where.

    Also picks up the one dependency that is not prose: the JSON Schema dialect
    each schema declares in `$schema`. A schema that says which dialect it
    speaks depends on that dialect's specification as surely as the text
    depends on the documents it names.
    """
    found = {}
    for path in normative_files():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()

        for m in CITATION.finditer(text):
            publisher, number = m.group(1), m.group(2)
            edition = (m.group(3) or "").lstrip(":")
            series = bool(m.group(4))
            name = f"{publisher} {number}" + (f":{edition}" if edition else "") \
                                           + (" series" if series else "")
            found.setdefault(name, {"publisher": publisher, "number": number,
                                    "edition": edition, "series": series,
                                    "where": set()})["where"].add(rel)

        if path.suffix == ".json":
            dialect = json.loads(text).get("$schema")
            if dialect:
                found.setdefault(dialect, {"publisher": "JSON Schema", "number": "",
                                           "edition": "", "series": False,
                                           "where": set()})["where"].add(rel)
    return found


def main() -> None:
    registry = load_registry()
    entries = registry.get("references", [])
    by_citation = {e.get("cited_as"): e for e in entries}
    # Keys beginning with $ are commentary, not entries. Counting one as a
    # mention would make the summary line report a number nobody declared.
    mentions = {k: v for k, v in registry.get("mentions_not_dependencies", {}).items()
                if not k.startswith("$")}
    problems = []

    cited = cited_documents()

    for name, info in sorted(cited.items()):
        publisher, number = info["publisher"], info["number"]
        where = ", ".join(sorted(info["where"]))

        # A passing mention is not a dependency, and must say so on the record.
        if name in mentions:
            if not mentions[name]:
                problems.append(
                    f"{name} is listed as a mention rather than a dependency, with "
                    f"no reason. Say why nothing depends on it, or register it.")
            continue

        # Asked first: a citation that names no document cannot be asked about
        # availability, and "not in the registry" would teach the wrong repair.
        if publisher.startswith("ISO") and number in MULTIPART \
                and "-" not in number and not info["series"]:
            problems.append(
                f"{name} (in {where}) is a multi-part standard and does not identify "
                f"a document. Cite a part and edition, or write \"{publisher} "
                f"{number} series\" if the statement concerns the family. Do not add "
                f"a registry entry: availability cannot be answered about a family.")
            continue

        entry = by_citation.get(name)
        if entry is None:
            problems.append(
                f"{name} (in {where}) is not declared in references/registry.json. "
                f"Add an entry with its `cited_as`, its identity and its availability, "
                f"so a reader can tell whether the claim can be checked.")
            continue

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

        # Identity before possession. An ISO number without an edition does not
        # name a document -- ISO revises under the same number -- so it cannot
        # be recorded as available or unavailable, only as unresolved.
        if publisher not in IMMUTABLE_PUBLISHERS and publisher != "JSON Schema" \
                and not info["edition"] and not info["series"] \
                and av in ("available", "unavailable"):
            problems.append(
                f"{name} (in {where}) names no edition, and {publisher} revises "
                f"under the same number, so the citation does not identify a "
                f"document. Its registry entry claims availability {av!r}, which "
                f"answers a question that cannot yet be asked. Either pin the "
                f"edition in the citation, or record it as `unresolved`.")

    for entry in entries:
        if entry.get("cited_as") not in cited:
            problems.append(
                f"{entry.get('id')}: declared in the registry and cited by no "
                f"normative artifact. Remove it, or cite it. A registry that "
                f"outlives its citations stops describing the specification.")

    if problems:
        for p in problems:
            print("error: " + p, file=sys.stderr)
        print(f"\n{len(problems)} problem(s) in the reference registry", file=sys.stderr)
        raise SystemExit(1)

    counts = {}
    for e in entries:
        counts[e["availability"]] = counts.get(e["availability"], 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
    print(f"every external document named by a normative artifact is accounted "
          f"for ({len(cited)} citations, {summary}, {len(mentions)} mention(s))")
    print("not checked here: whether a document supports what the specification "
          "attributes to it -- that needs the document open, and is a separate question")


if __name__ == "__main__":
    main()
