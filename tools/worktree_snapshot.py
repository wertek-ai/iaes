#!/usr/bin/env python3
"""Record the repository's state by content, so a change to it can be seen.

Used by `tests/conftest.py` to check that the test suite leaves the repository
exactly as it found it. Two decisions about how it measures, and each one is a
defect the obvious version has:

**By content, not by status.** Comparing two sets of `git status --porcelain`
lines catches a suite that dirties a clean tree, and misses the case the design
exists to tolerate -- a developer who starts with `M GOVERNANCE.md` at bytes A
and ends with `M GOVERNANCE.md` at bytes B produces the same line both times,
so the difference of the sets is empty. It misses the worse direction too: a
fixture that "restores" a file to HEAD and destroys uncommitted work leaves
*fewer* lines, and that difference is empty as well.

**Not through `git diff`.** The defect this exists to catch is one Git can be
configured to normalise away: with `core.autocrlf` or a `text=auto` attribute a
file rewritten with CRLF can show no diff at all. Asking Git whether a file
changed would consult the same normalisation that hides it.

The tree may therefore start dirty and end dirty. It has to be the *same*
dirty, byte for byte.

SPDX-License-Identifier: CC-BY-4.0
"""

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ADVICE = (
    "A fixture that restores a file must restore its BYTES. Pass "
    'newline="\\n" to write_text: without it the restore is text-equal '
    "and byte-different on Windows."
)


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT,
                          capture_output=True, text=True).stdout


def _paths() -> list:
    """Everything Git would notice: tracked, plus untracked that is not ignored."""
    listed = _git("ls-files", "-z") + _git("ls-files", "--others",
                                           "--exclude-standard", "-z")
    return sorted({p for p in listed.split("\0") if p})


def _digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (FileNotFoundError, IsADirectoryError, PermissionError, OSError):
        return "absent"


def snapshot() -> dict:
    """The working tree and the index, by content.

    The index is included because a test that stages something and forgets to
    unstage it leaves the repository changed without touching a single byte in
    the working tree.
    """
    return {
        "files": {p: _digest(ROOT / p) for p in _paths()},
        "index": _git("ls-files", "--stage"),
    }


def differences(before: dict, after: dict) -> list:
    """What changed between two snapshots, phrased as a repair."""
    out = []
    if before["index"] != after["index"]:
        out.append("the git index was left staged differently")
    for name in sorted(set(before["files"]) | set(after["files"])):
        was = before["files"].get(name, "absent")
        now = after["files"].get(name, "absent")
        if was == now:
            continue
        if was == "absent":
            out.append(f"{name}: created and not removed")
        elif now == "absent":
            out.append(f"{name}: deleted and not restored")
        else:
            out.append(f"{name}: {was[:12]} -> {now[:12]}")
    return out


if __name__ == "__main__":
    state = snapshot()
    print(f"{len(state['files'])} paths under content check")
    if len(sys.argv) > 1 and sys.argv[1] == "--print":
        for name, digest in state["files"].items():
            print(f"{digest[:12]}  {name}")
