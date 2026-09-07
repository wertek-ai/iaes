"""Armed at zero, on the case the first version of this guard went green for.

The guard's promise is that the suite leaves the repository as it found it --
*including* when it found it dirty. The obvious implementation compares two
sets of `git status --porcelain` lines, passes the defect it was written for,
and cannot see any of these:

    before   M GOVERNANCE.md   bytes A        the developer's own work
    after    M GOVERNANCE.md   bytes B        the suite rewrote it
             ^ same line, so the set difference is empty

    before   M GOVERNANCE.md                  the developer's own work
    after    <clean>                          the suite destroyed it
             ^ fewer lines, so the difference in that direction is empty too

Each is armed here, both against the decision function and end to end through a
nested pytest session, because a guard that is only unit-tested has not been
shown to run.

SPDX-License-Identifier: CC-BY-4.0
"""

import os
import subprocess
import sys
from pathlib import Path

import importlib.util

import pytest


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The same file conftest.py measures with, loaded the same way: `tools/` is a
# directory of scripts, not a package, and pytest does not put `tests/` on
# sys.path reliably enough to import the conftest by name.
worktree = _load("iaes_worktree_snapshot",
                 Path(__file__).resolve().parent.parent / "tools" / "worktree_snapshot.py")

ROOT = worktree.ROOT
snapshot = worktree.snapshot
differences = worktree.differences

GOVERNANCE = ROOT / "GOVERNANCE.md"
PROBE = ROOT / "tests" / "test_probe_leaves_repo_dirty.py"

PROBE_SOURCE = '''"""Written by test_worktree_snapshot.py and deleted by it. Not a real test."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_the_probe_edits_a_normative_artifact():
    p = ROOT / "GOVERNANCE.md"
    original = p.read_bytes()
    p.write_bytes(original.replace(b"\\n", b"\\r\\n", 1))
    if os.environ["PROBE_MODE"] == "restore_exact":
        p.write_bytes(original)
'''


def porcelain() -> set:
    out = subprocess.run(["git", "status", "--porcelain", "--", "."],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return set(out.splitlines())


@pytest.fixture
def governance():
    """Restores GOVERNANCE.md byte-for-byte however the test leaves it."""
    original = GOVERNANCE.read_bytes()
    try:
        yield original
    finally:
        GOVERNANCE.write_bytes(original)


def test_a_dirty_file_rewritten_in_place_is_seen(governance):
    """The case the porcelain version went green for."""
    GOVERNANCE.write_bytes(governance + b"\n<!-- the developer's own work -->\n")
    before, status_before = snapshot(), porcelain()

    GOVERNANCE.write_bytes(governance + b"\n<!-- what the suite left -->\n")
    after, status_after = snapshot(), porcelain()

    assert status_before == status_after, (
        "this test is only meaningful while both states produce the same "
        "porcelain line; if that stops being true, rewrite it")
    changed = differences(before, after)
    assert any("GOVERNANCE.md" in line for line in changed), changed


def test_restoring_it_to_the_same_bytes_is_green(governance):
    """Dirty in, dirty out, and the guard stays quiet."""
    work = governance + b"\n<!-- the developer's own work -->\n"
    GOVERNANCE.write_bytes(work)
    before = snapshot()

    GOVERNANCE.write_bytes(governance)          # a fixture borrows the file
    GOVERNANCE.write_bytes(work)                # and gives it back exactly

    assert differences(before, snapshot()) == []


def test_destroying_uncommitted_work_is_seen(governance):
    """A 'restore' to HEAD is not a restore if HEAD is not what was there."""
    GOVERNANCE.write_bytes(governance + b"\n<!-- the developer's own work -->\n")
    before = snapshot()

    GOVERNANCE.write_bytes(governance)
    changed = differences(before, snapshot())

    assert any("GOVERNANCE.md" in line for line in changed), changed


def test_something_left_staged_is_seen():
    """No byte in the working tree changes when a test forgets to unstage."""
    stray = ROOT / "tests" / "_staged_probe.txt"
    stray.write_bytes(b"probe\n")
    before = snapshot()
    try:
        subprocess.run(["git", "add", str(stray)], cwd=ROOT, capture_output=True)
        assert differences(before, snapshot()) == ["the git index was left staged differently"]
    finally:
        subprocess.run(["git", "rm", "--cached", "-q", str(stray)],
                       cwd=ROOT, capture_output=True)
        stray.unlink(missing_ok=True)


@pytest.mark.parametrize("mode, expected", [
    ("change", 1),
    ("restore_exact", 0),
])
def test_a_nested_session_fails_when_it_leaves_the_repository_changed(
        governance, mode, expected):
    """End to end, starting dirty -- the scenario the design must tolerate.

    Unit tests prove the decision; this proves pytest reaches it.
    """
    GOVERNANCE.write_bytes(governance + b"\n<!-- the developer's own work -->\n")
    PROBE.write_text(PROBE_SOURCE, encoding="utf-8", newline="\n")
    env = dict(os.environ, PROBE_MODE=mode, PYTHONPATH=str(ROOT / "src"))
    try:
        run = subprocess.run(
            [sys.executable, "-m", "pytest", str(PROBE), "-q",
             "-p", "no:cacheprovider"],
            cwd=ROOT, capture_output=True, text=True, env=env)
        assert run.returncode == expected, run.stdout[-2000:] + run.stderr[-2000:]
        if expected:
            assert "did not restore it" in run.stdout + run.stderr
            assert "GOVERNANCE.md" in run.stdout + run.stderr
    finally:
        PROBE.unlink(missing_ok=True)
