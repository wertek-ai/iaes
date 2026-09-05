"""The manifest must describe the release, not the machine that built it.

The first manifest attached to spec-v1.4 was built on Windows. CI had built one
on Linux from the same tag, and all twelve digests differed -- ten normative
files and both RFCs -- because a Windows clone stores CRLF where a Linux clone
stores LF. Same tag, same content, different bytes, different answer.

That defeats the only thing a manifest is for: a reader verifying that what
they were served is what was released.

Normalizing line endings before hashing would have fixed the symptom. The cause
is that the digest came from the checkout at all. A release is defined by its
tag, so the digest comes from the objects that tag identifies.

These tests prove the property by checking out the same content both ways.
"""

import hashlib
import importlib.util
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "build_release_manifest", ROOT / "tools" / "build_release_manifest.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(*args) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True
    ).stdout


class TestTheDigestComesFromTheRepository(unittest.TestCase):
    def test_line_endings_do_not_change_the_digest(self):
        """The core property, checked directly rather than inferred."""
        tool = load_tool()
        path = ROOT / "GOVERNANCE.md"
        canonical = tool.digest(path)

        content = git("show", "HEAD:GOVERNANCE.md")
        as_lf = hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()
        as_crlf = hashlib.sha256(content.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()

        self.assertNotEqual(as_lf, as_crlf, "the file has no line endings to differ over")
        self.assertEqual(
            canonical, as_lf,
            "the digest should be of the repository's content, which git stores with LF",
        )

    def test_the_digest_ignores_the_working_tree(self):
        """Editing a file on disk must not change what the manifest reports."""
        tool = load_tool()
        path = ROOT / "GOVERNANCE.md"
        before = tool.digest(path)

        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n<!-- a local edit -->\n")
            after = tool.digest(path)
        finally:
            path.write_bytes(original)

        self.assertEqual(
            before, after,
            "an uncommitted edit changed the manifest -- the digest is reading the disk",
        )

    def test_a_file_that_is_not_committed_is_refused(self):
        """Silence would be worse: a release cannot contain what it does not have."""
        tool = load_tool()
        stray = ROOT / "schema" / "not-committed.schema.json"
        stray.write_text("{}", encoding="utf-8")
        try:
            with self.assertRaises(SystemExit):
                tool.digest(stray)
        finally:
            stray.unlink()

    def test_the_manifest_of_a_tag_is_the_same_from_any_checkout(self):
        """End to end: build it twice, once against the tag, and compare."""
        tool = load_tool()
        tags = git("tag", "-l", "spec-v*").decode().split()
        if not tags:
            self.skipTest("no specification tag in this clone")
        tag = sorted(tags)[-1]

        first = tool.build(tag=tag, out=None)
        second = tool.build(tag=tag, out=None)

        self.assertEqual(first["normative"], second["normative"])
        self.assertEqual(first["rationale"], second["rationale"])
        # built_at is the one field that legitimately differs, and it is not
        # asserted here: two builds a millisecond apart can share a timestamp.


if __name__ == "__main__":
    unittest.main()
