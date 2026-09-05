#!/usr/bin/env python3
"""Assemble — and verify — what a specification release consists of.

A specification release is one indivisible object: the specification, the
governance document, the schemas and the accepted RFCs, published under one
tag. An implementation release is a package that declares which specification
it implements. They were never distinguished because only the second existed,
and the cost showed: the site served v1.3 while the packages emitted 1.4 and
nothing reported it.

This script is the check that makes them agree, and the manifest that records
what agreed. It publishes nothing.

  --check    fail if the tag, the specification and the packages disagree
  --out      write the manifest

Dependency-free on purpose: the compatibility guard next door is too, and a
release tool that needs an install is a release tool that stops running.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TAG_PREFIX = "spec-v"

# The normative set. A specification release is exactly this, and the manifest
# records a digest of each file so a reader can verify what they were served.
NORMATIVE = [
    "IAES_SPEC.md",
    "GOVERNANCE.md",
]
NORMATIVE_GLOBS = [
    "schema/*.schema.json",
    "rfc/*.md",
]

# Every package declares which specification it implements. The first two
# components must match the specification version; the third is the package's
# own release number and is deliberately free.
PACKAGES = {
    "npm/package.json": "json",
    "node-red/package.json": "json",
    "n8n-nodes/package.json": "json",
    "pyproject.toml": "toml",
}


def spec_version_from_document() -> str:
    title = (ROOT / "IAES_SPEC.md").read_text(encoding="utf-8").split("\n", 1)[0]
    m = re.search(r"v(\d+\.\d+)\s*$", title)
    if not m:
        raise SystemExit(f"no version in the specification title: {title!r}")
    return m.group(1)


def spec_version_from_sdk() -> str:
    src = (ROOT / "src" / "iaes" / "envelope.py").read_text(encoding="utf-8")
    m = re.search(r'^SPEC_VERSION\s*=\s*["\']([^"\']+)["\']', src, re.M)
    if not m:
        raise SystemExit("SPEC_VERSION not found in the Python SDK")
    return m.group(1)


def package_versions() -> dict:
    out = {}
    for rel, kind in PACKAGES.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        if kind == "json":
            out[rel] = json.loads(text)["version"]
        else:
            m = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.M)
            if not m:
                raise SystemExit(f"no version in {rel}")
            out[rel] = m.group(1)
    return out


def major_minor(version: str) -> str:
    return ".".join(version.split(".")[:2])


def normative_files() -> list:
    files = [ROOT / p for p in NORMATIVE]
    for pattern in NORMATIVE_GLOBS:
        files.extend(sorted(ROOT.glob(pattern)))
    missing = [f for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"normative set is incomplete: {missing}")
    return files


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(tag: str | None) -> str:
    """Every surface must name the same specification version."""
    document = spec_version_from_document()
    sdk = spec_version_from_sdk()
    problems = []

    if sdk != document:
        problems.append(
            f"the specification titles itself {document} but the SDK emits spec_version {sdk}"
        )

    if tag:
        if not tag.startswith(TAG_PREFIX):
            problems.append(
                f"{tag!r} is not a specification tag — it must start with {TAG_PREFIX!r}"
            )
        else:
            tagged = tag[len(TAG_PREFIX):]
            if tagged != document:
                problems.append(
                    f"tag {tag!r} says {tagged} but the specification says {document}"
                )
            if len(tagged.split(".")) != 2:
                problems.append(
                    f"a specification version has two components; {tagged!r} has "
                    f"{len(tagged.split('.'))}. Three components is an implementation release."
                )

    # Packages implement a specification; they do not have one of their own.
    for rel, version in package_versions().items():
        if major_minor(version) != document:
            problems.append(
                f"{rel} is {version}, which implements {major_minor(version)}, "
                f"not the {document} being released"
            )

    if problems:
        for p in problems:
            print(f"error: {p}", file=sys.stderr)
        raise SystemExit(1)

    return document


def build(tag: str | None, out: Path | None) -> dict:
    version = check(tag)
    files = normative_files()
    manifest = {
        "specification_version": version,
        "tag": tag,
        "built_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "normative": {
            str(f.relative_to(ROOT)).replace("\\", "/"): digest(f) for f in files
        },
        "implementations": {
            rel: {"version": v, "implements": major_minor(v)}
            for rel, v in package_versions().items()
        },
        "note": (
            "A specification release is this set of files under this tag. "
            "The implementations listed here declare which specification they "
            "implement; they are released separately and carry no specification "
            "of their own."
        ),
    }
    if out:
        out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tag", help="the specification tag being released, e.g. spec-v1.4")
    ap.add_argument("--check", action="store_true", help="verify agreement and stop")
    ap.add_argument("--out", type=Path, help="write the manifest here")
    args = ap.parse_args()

    if args.check:
        version = check(args.tag)
        print(f"every surface agrees on IAES {version}")
        return

    manifest = build(args.tag, args.out)
    print(
        f"IAES {manifest['specification_version']} — "
        f"{len(manifest['normative'])} normative files"
    )


if __name__ == "__main__":
    main()
