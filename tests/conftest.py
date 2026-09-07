"""The suite must leave the repository exactly as it found it.

Several tests break a normative artifact on purpose to watch a guard reject it,
and restore it afterwards. Restoring the *text* is not enough: `write_text`
opens in text mode, so on Windows every LF came back as CRLF and the file was
left modified with identical content. Nobody noticed, because `git diff` shows
no changed lines -- and a tree that is quietly dirty is how unrelated files get
swept into a commit.

The comparison is by content and deliberately not through `git diff`; the
reasoning is in `tools/worktree_snapshot.py`, which does the measuring. This
file only decides what to do about it.

SPDX-License-Identifier: CC-BY-4.0
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    """Load a tool by path. `tools/` is a directory of scripts, not a package,
    and putting it on sys.path to import one file would shadow names for every
    test in the suite."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


worktree = _load("iaes_worktree_snapshot", ROOT / "tools" / "worktree_snapshot.py")


def pytest_sessionstart(session):
    session.iaes_snapshot = worktree.snapshot()


def pytest_sessionfinish(session, exitstatus):
    before = getattr(session, "iaes_snapshot", None)
    if before is None:
        return
    left = worktree.differences(before, worktree.snapshot())
    if left:
        raise RuntimeError(
            "the test suite changed the repository and did not restore it:\n"
            + "\n".join(left) + "\n\n" + worktree.ADVICE
        )
