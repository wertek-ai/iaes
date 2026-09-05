#!/usr/bin/env python3
"""Assemble — and verify — what a specification release consists of.

A specification release is one indivisible object published under one tag: the
specification, the governance document and the schemas, which govern behaviour,
plus the accepted RFCs, which record why. They travel together and each carries
a digest; only their authority differs.

An implementation release is a package that declares which specification it
implements. The two were never distinguished because only the second existed,
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
import subprocess
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
]

# Accepted RFCs travel in the same release and get the same digest treatment,
# but they are not authority. RFC-000 settled this: once an RFC is incorporated
# it answers why a decision was made, not how IAES behaves. Two simultaneous
# authorities is how RFC-001 and the envelope schema came to disagree about
# whether correlation_id is required.
RATIONALE_GLOBS = [
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


def rationale_files() -> list:
    files = []
    for pattern in RATIONALE_GLOBS:
        files.extend(sorted(ROOT.glob(pattern)))
    return files


def digest(path: Path, ref: str = "HEAD") -> str:
    """SHA-256 of the file's content *in the repository*, not on this disk.

    Hashing the working tree made the manifest depend on the checkout: a Windows
    clone stores CRLF where a Linux clone stores LF, so the same tag produced
    twelve different digests on the two machines. The first manifest attached to
    spec-v1.4 was built on Windows and recorded digests nobody else could
    reproduce -- which defeats the only thing a manifest is for.

    A release is defined by its tag, so the digest comes from the objects that
    tag identifies. Normalizing line endings would have fixed the symptom and
    left the cause: the answer would still have come from the checkout.
    """
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    try:
        content = subprocess.run(
            ["git", "show", f"{ref}:{rel}"],
            cwd=ROOT, check=True, capture_output=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise SystemExit(
            f"cannot read {rel} from {ref}: {e}. The manifest describes a release, "
            f"so every file in it must be committed."
        )
    return hashlib.sha256(content).hexdigest()


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
    # The tag when there is one, so the manifest describes the release rather
    # than whatever happens to be checked out.
    ref = tag if tag else "HEAD"
    manifest = {
        "specification_version": version,
        "tag": tag,
        "built_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "normative": {
            str(f.relative_to(ROOT)).replace("\\", "/"): digest(f, ref) for f in files
        },
        "rationale": {
            str(f.relative_to(ROOT)).replace("\\", "/"): digest(f, ref)
            for f in rationale_files()
        },
        "implementations": {
            rel: {"version": v, "implements": major_minor(v)}
            for rel, v in package_versions().items()
        },
        "note": (
            "Digests are SHA-256 of the content in the repository at this tag, not of ""the files as they appear in a checkout -- line endings differ by platform ""and the digest must not. ""A specification release is these files under this tag; `normative` "
            "governs behaviour and `rationale` records why. "
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
    # Worded so the second number cannot be read as a second kind of normative
    # file: the RFCs travel in the release and carry a digest, but they do not
    # govern behaviour.
    print(
        f"IAES {manifest['specification_version']} — "
        f"{len(manifest['normative'])} normative files "
        f"+ {len(manifest['rationale'])} RFCs (rationale)"
    )


if __name__ == "__main__":
    main()
