"""tools/check_schema_compat.py: a schema in no release yet may be narrowed; a released one may not.

GOVERNANCE.md 4 is a promise between releases. The guard used to compare the
tree with the previous commit only, so it would have blocked tightening a
schema that was added in the same unreleased version -- which is exactly when a
review finds what to tighten (the asset.state pre-cut, 2026-10-07). It now
reads the last release tag. These cases build a throwaway repository and run
the real tool against it, so they test the guard and not a copy of its logic.

Armed both ways: the same narrowing BLOCKS on a released schema (the guard
still guards), and blocks on the unreleased one when no release tag exists (it
fails closed instead of guessing).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "check_schema_compat.py"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is required")

LOOSE = {"type": "object", "properties": {"data": {"type": "object", "properties": {
    "kind": {"type": ["string", "null"], "enum": ["a", "b", None]}}}}}
TIGHT = {"type": "object", "properties": {"data": {"type": "object", "properties": {
    "kind": {"type": "string", "enum": ["a", "b"]}}}}}


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _write(repo, name, schema):
    (repo / "schema" / name).write_text(json.dumps(schema), encoding="utf-8")


def _repo(tmp_path, tag_release: bool) -> Path:
    """released.schema.json is in the release; fresh.schema.json was added after it."""
    repo = tmp_path / "repo"
    (repo / "schema").mkdir(parents=True)
    (repo / "IAES_SPEC.md").write_text("# IAES v2.0\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    _write(repo, "released.schema.json", LOOSE)
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "release")
    if tag_release:
        _git(repo, "tag", "spec-v2.0")
    _write(repo, "fresh.schema.json", LOOSE)
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "add a schema after the release")
    return repo


def _check(repo):
    out = subprocess.run([sys.executable, str(TOOL), "--baseline", "HEAD"],
                         cwd=repo, capture_output=True, text=True)
    return out.returncode, out.stdout + out.stderr


def test_an_unreleased_schema_may_be_narrowed(tmp_path):
    repo = _repo(tmp_path, tag_release=True)
    _write(repo, "fresh.schema.json", TIGHT)
    code, out = _check(repo)
    assert code == 0, out
    assert "in no release up to spec-v2.0" in out, out
    assert "type narrowed" in out, "the narrowing is still reported, only not blocking"


def test_a_released_schema_may_not(tmp_path):
    repo = _repo(tmp_path, tag_release=True)
    _write(repo, "released.schema.json", TIGHT)
    code, out = _check(repo)
    assert code == 1, out
    assert "Blocked" in out, out


def test_without_a_release_tag_the_guard_fails_closed(tmp_path):
    repo = _repo(tmp_path, tag_release=False)
    _write(repo, "fresh.schema.json", TIGHT)
    code, out = _check(repo)
    assert code == 1, out
    assert "none reachable from HEAD" in out, out
