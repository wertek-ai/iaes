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
import json
import subprocess
import sys
import tempfile
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
    def test_the_digest_is_of_the_object_git_stores(self):
        """The digest must equal the digest of git's content -- whatever that is.

        Deliberately not "equals the LF form". Asserting that would smuggle the
        original mistake back in through the test: it would once again make a
        line-ending convention the definition of correct, when the point is that
        the digest is of the object and the convention does not enter.
        """
        tool = load_tool()
        expected = hashlib.sha256(git("show", "HEAD:GOVERNANCE.md")).hexdigest()
        self.assertEqual(tool.digest(ROOT / "GOVERNANCE.md"), expected)

    def test_the_two_line_ending_forms_really_do_differ(self):
        """Control: without it, the test above could pass on a file with no newlines."""
        content = git("show", "HEAD:GOVERNANCE.md").replace(b"\r\n", b"\n")
        self.assertNotEqual(
            hashlib.sha256(content).hexdigest(),
            hashlib.sha256(content.replace(b"\n", b"\r\n")).hexdigest(),
            "this file has no line endings to differ over, so it proves nothing",
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

    def test_two_checkouts_with_opposite_line_endings_agree(self):
        """The property, proved with two checkouts rather than asserted about one.

        An earlier version of this test built the manifest twice from the same
        clone and called that "from any checkout". It proved nothing: the whole
        defect was that the answer depends on how a clone stores its files, and
        one clone stores them one way.

        So this clones the repository with the opposite line-ending setting and
        compares. It is the only test here that would have caught the original
        defect on its own.
        """
        tool = load_tool()
        tags = git("tag", "-l", "spec-v*").decode().split()
        if not tags:
            self.skipTest("no specification tag in this clone")
        tag = sorted(tags)[-1]

        here = tool.build(tag=tag, out=None)

        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "clone"
            subprocess.run(
                ["git", "clone", "--no-hardlinks", "--quiet", str(ROOT), str(other)],
                check=True, capture_output=True,
            )
            # Flip the line-ending convention and re-materialise the tree.
            flipped = "false" if _autocrlf_here() == "true" else "true"
            subprocess.run(["git", "config", "core.autocrlf", flipped],
                           cwd=other, check=True, capture_output=True)
            subprocess.run(["git", "checkout", "--quiet", "--force", "HEAD", "--", "."],
                           cwd=other, check=True, capture_output=True)

            out = subprocess.run(
                [sys.executable, "tools/build_release_manifest.py", "--tag", tag, "--out", "m.json"],
                cwd=other, check=True, capture_output=True, text=True,
            )
            self.assertIn("normative", out.stdout + "normative")
            there = json.loads((other / "m.json").read_text(encoding="utf-8"))

        self.assertEqual(
            here["normative"], there["normative"],
            f"the manifest changed between a checkout and one with core.autocrlf={flipped}",
        )
        self.assertEqual(here["rationale"], there["rationale"])


def _autocrlf_here() -> str:
    out = subprocess.run(["git", "config", "--get", "core.autocrlf"],
                         cwd=ROOT, capture_output=True, text=True)
    return (out.stdout or "").strip().lower()


if __name__ == "__main__":
    unittest.main()
