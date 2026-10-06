#!/usr/bin/env python3
"""The reference scenarios, in Ignition.

The scenario IS `tags.json` -- the tag export an integrator imports into an
Ignition 8.3 Gateway. This script does not re-tell the story: it reads the
`valueChanged` script of the `run` tag out of that file, unchanged, and executes
it the way the Gateway does (as the body of `valueChanged(tag, tagPath,
previousValue, currentValue, initialChange, missedEvents)`), then prints what
the script wrote to `last_events`. `tests/test_reference_scenarios.py` checks
the output against `scenarios/fixture.json` alongside the other
implementations.

    python scenarios/ignition/run.py            # prints the events
    python scenarios/ignition/run.py out.json   # writes them

### What is substituted, and what that leaves unproven

CI cannot run an Ignition Gateway. The one substitution is `system.*`: tag
reads and writes are served from the defaults in `tags.json`, the logger
records, `invokeAsynchronous` runs the function at once, and `httpClient` is
not reachable because `receiver_url` is empty -- if the script tried to POST,
this runner fails. Everything else is the script's own code on CPython.

What this does NOT prove: that Jython 2.7 produces the same bytes (the
`content_hash` depends on `json.dumps` and float formatting), that the tag
types import, or that the event script fires. Those were checked once, on a
real Gateway, and are recorded in `README.md` next to this file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TAGS = Path(__file__).with_name("tags.json")


def fail(message: str) -> None:
    sys.stderr.write(f"reference scenarios (ignition): {message}\n")
    sys.exit(1)


class Quality:
    def __init__(self, good: bool = True):
        self._good = good

    def isGood(self) -> bool:  # noqa: N802 -- Ignition's name
        return self._good


class QualifiedValue:
    def __init__(self, value):
        self.value = value
        self.quality = Quality(True)


class Logger:
    def __init__(self):
        self.lines = []

    def _log(self, level, msg):
        self.lines.append((level, str(msg)))

    def info(self, msg):
        self._log("INFO", msg)

    def warn(self, msg):
        self._log("WARN", msg)

    def error(self, msg):
        self._log("ERROR", msg)


class System:
    """The part of Ignition's `system.*` the script uses, and nothing else."""

    def __init__(self, folder: dict):
        root = f"[default]{folder['name']}/"
        self.values = {root + t["name"]: t.get("value") for t in folder["tags"]}
        self.logger = Logger()
        self.posts = []
        outer = self

        class Tag:
            @staticmethod
            def readBlocking(paths):  # noqa: N802
                missing = [p for p in paths if p not in outer.values]
                if missing:
                    fail(f"the script reads tags that tags.json does not define: {missing}")
                return [QualifiedValue(outer.values[p]) for p in paths]

            @staticmethod
            def writeBlocking(paths, values):  # noqa: N802
                for p, v in zip(paths, values):
                    if p not in outer.values:
                        fail(f"the script writes a tag that tags.json does not define: {p}")
                    outer.values[p] = v

        class Util:
            @staticmethod
            def getLogger(name):  # noqa: N802
                return outer.logger

            @staticmethod
            def invokeAsynchronous(fn):  # noqa: N802
                fn()

        class Net:
            @staticmethod
            def httpClient(**_):  # noqa: N802
                outer.posts.append("httpClient")
                fail("the script tried to POST although receiver_url is empty")

        self.tag, self.util, self.net = Tag, Util, Net
        self.root = root


def main() -> None:
    if not TAGS.exists():
        fail(f"{TAGS.name} is missing: run build_tags.py")
    folder = json.loads(TAGS.read_text(encoding="utf-8"))
    run_tag = next((t for t in folder["tags"] if t["name"] == "run"), None)
    scripts = [s for s in (run_tag or {}).get("eventScripts", []) if s.get("eventid") == "valueChanged"]
    if not scripts:
        fail("tags.json has no valueChanged script on the `run` tag")

    system = System(folder)
    source = ("def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):\n"
              + scripts[0]["script"])
    namespace = {"system": system}
    exec(compile(source, "tags.json:run.valueChanged", "exec"), namespace)
    namespace["valueChanged"](None, system.root + "run", QualifiedValue(False), QualifiedValue(True), False, False)

    errors = [m for level, m in system.logger.lines if level == "ERROR"]
    if errors:
        fail("the script logged an error: " + "; ".join(errors))
    if system.values[system.root + "run"] is not False:
        fail("the script did not set `run` back to false")
    raw = system.values[system.root + "last_events"]
    if not raw:
        fail("the script wrote nothing to last_events")
    events = json.loads(raw)

    out = json.dumps(events, indent=2)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(out + "\n", encoding="utf-8")
    else:
        print(out)


if __name__ == "__main__":
    main()
