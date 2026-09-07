"""The suite must leave the repository exactly as it found it.

Several tests break a normative artifact on purpose to watch a guard reject it,
and restore it afterwards. Restoring the *text* is not enough: `write_text`
opens in text mode, so on Windows every LF came back as CRLF and the file was
left modified with identical content. Nobody noticed, because `git diff` shows
no changed lines -- and a tree that is quietly dirty is how unrelated files get
swept into a commit.

Measured as a difference rather than against a clean tree. A developer's own
uncommitted work is not this guard's business, and a guard that fires on it
would be switched off within a week.

SPDX-License-Identifier: CC-BY-4.0
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ADVICE = (
    "A fixture that restores a file must restore its BYTES. Pass "
    'newline="\\n" to write_text: without it the restore is text-equal '
    "and byte-different on Windows."
)


def _worktree() -> set:
    out = subprocess.run(["git", "status", "--porcelain", "--", "."],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return set(out.splitlines())


def pytest_sessionstart(session):
    session.iaes_worktree_before = _worktree()


def pytest_sessionfinish(session, exitstatus):
    before = getattr(session, "iaes_worktree_before", None)
    if before is None:
        return
    left = sorted(_worktree() - before)
    if left:
        raise RuntimeError(
            "the test suite changed tracked files and did not restore them:\n"
            + "\n".join(left) + "\n\n" + ADVICE
        )
