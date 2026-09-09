"""Every reference scenario, in every language, produces the same events.

That is the whole claim of the battery -- **the workflow changes, the event
meaning does not** -- and it is worth nothing unless something checks it. So
this runs the Python and TypeScript scenarios and compares both against
`scenarios/fixture.json`.

What is compared is what a consumer acts on. `event_id` is a fresh UUID and
`timestamp` is the moment of emission: two correct implementations differ there
and are still the same event. Those fields are listed as volatile IN THE
FIXTURE, with the reason, rather than hidden in this file -- a reader of the
fixture can see what is not being checked without reading the test.

The correlation STRUCTURE is checked instead of the correlation values: every
event in the chain carries the same `correlation_id`, and each one that follows
another points back at it with `source_event_id`. That is the property a
consumer relies on, and it survives the ids being different.

Writing these scenarios found two defects in the TypeScript SDK that its own
tests could not see, because they build events with the model classes and never
hand the SDK's own type back to it. Both are fixed in 2.0.1.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "scenarios" / "fixture.json"
PY_SCENARIO = ROOT / "scenarios" / "python" / "reference_scenarios.py"
TS_SCENARIO = ROOT / "scenarios" / "typescript" / "reference-scenarios.ts"
TSC = ROOT / "npm" / "node_modules" / ".bin" / "tsc"
DIST = ROOT / "npm" / "dist" / "index.js"


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def volatile() -> set:
    return {k for k in fixture()["volatile"] if not k.startswith("$")}


def python_events() -> list:
    import sys

    sys.path.insert(0, str(ROOT / "scenarios" / "python"))
    sys.path.insert(0, str(ROOT / "src"))
    import reference_scenarios

    return reference_scenarios.run()


def typescript_events(tmp_path: Path) -> list:
    """Compile the TypeScript scenario against the built SDK, then run it.

    Compiled rather than run through a TS loader on purpose: the compiler is
    half the test. The scenario must typecheck in strict mode with no casts --
    the defects it found were type errors, and a loader that strips types would
    not have seen them.
    """
    if not DIST.exists():
        pytest.fail(
            "npm/dist is not built. This test compiles the TypeScript scenario "
            "against it; run `npm run build` in npm/. Reported rather than "
            "skipped: a skipped check is one that stopped checking."
        )
    # On Windows the extensionless `tsc` is a shell script, not an executable:
    # running it raises WinError 193. The .cmd shim is the one that runs.
    candidates = ([TSC.with_suffix(".cmd"), TSC] if sys.platform == "win32"
                  else [TSC])
    tsc_path = next((c for c in candidates if c.exists()), None)
    if tsc_path is None:
        pytest.fail(
            "npm/node_modules/.bin/tsc is missing. Run `npm ci` in npm/."
        )

    source = TS_SCENARIO.read_text(encoding="utf-8")
    entry = tmp_path / "scenario.ts"
    entry.write_text(source.replace('"@iaes/sdk"', f'"{DIST.as_posix()}"'),
                     encoding="utf-8")

    build = subprocess.run(
        [str(tsc_path), "--target", "es2022", "--module", "nodenext",
         "--moduleResolution", "nodenext", "--strict", "--skipLibCheck",
         "--types", "node", "--typeRoots",
         str(ROOT / "npm" / "node_modules" / "@types"),
         "--outDir", str(tmp_path / "out"), str(entry)],
        capture_output=True, text=True, timeout=180,
    )
    assert build.returncode == 0, (
        "the TypeScript scenario does not compile in strict mode:\n"
        + build.stdout + build.stderr
    )

    run = subprocess.run(["node", str(tmp_path / "out" / "scenario.js")],
                         capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout)


def workflow_events(tool: str) -> list:
    """Run a workflow tool's reference scenario and return what it emitted.

    The scenario for Node-RED and n8n is the importable file (flow.json,
    workflow.json); `scenarios/<tool>/run.js` executes it and prints the
    events. Each runner reports its own missing precondition -- the Node-RED
    runtime, the compiled n8n nodes -- on stderr and exits non-zero, and that
    message is the failure here. Reported rather than skipped.
    """
    run = subprocess.run(["node", str(ROOT / "scenarios" / tool / "run.js")],
                         cwd=ROOT, capture_output=True, text=True, timeout=180)
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout)


def nodered_events() -> list:
    return workflow_events("node-red")


def n8n_events() -> list:
    return workflow_events("n8n")


def stable(event: dict, drop: set) -> dict:
    return {k: v for k, v in event.items() if k not in drop}


def check_against_fixture(events: list, language: str) -> None:
    fx = fixture()
    drop = volatile()
    expected = fx["events"]

    assert len(events) == len(expected), (
        f"{language} produced {len(events)} events, the fixture describes "
        f"{len(expected)}"
    )

    for got, want in zip(events, expected):
        where = f"{language} / {want['scenario']}"
        assert got["event_type"] == want["event_type"], where
        assert got["source"] == want["source"], where
        assert got["spec_version"] == fx["spec_version"], where
        assert got["asset"]["asset_id"] == fx["asset"]["asset_id"], where
        for key, value in want["data"].items():
            assert got["data"].get(key) == value, f"{where}: data.{key}"

    # The chain, not the values.
    correlation = {e["correlation_id"] for e in events}
    assert len(correlation) == 1, (
        f"{language}: the story is one chain and carries one correlation_id, "
        f"found {len(correlation)}"
    )
    by_scenario = dict(zip([e["scenario"] for e in expected], events))
    for want, got in zip(expected, events):
        if "follows" not in want:
            continue
        parent = by_scenario[want["follows"]]
        assert got.get("source_event_id") == parent["event_id"], (
            f"{language} / {want['scenario']} must point back at "
            f"{want['follows']}"
        )

    # And the volatile fields really are present and really do differ from the
    # fixture's description -- otherwise "excluded from the comparison" would
    # be hiding a field nobody emits.
    for got in events:
        assert got.get("event_id"), f"{language}: every event carries an event_id"
        assert got.get("timestamp"), f"{language}: every event carries a timestamp"
    ids = [e["event_id"] for e in events]
    assert len(set(ids)) == len(ids), f"{language}: event_id must be unique per event"


def test_python_scenarios_match_the_fixture():
    check_against_fixture(python_events(), "python")


def test_typescript_scenarios_match_the_fixture(tmp_path):
    check_against_fixture(typescript_events(tmp_path), "typescript")


def test_nodered_scenarios_match_the_fixture():
    check_against_fixture(nodered_events(), "node-red")


def test_n8n_scenarios_match_the_fixture():
    check_against_fixture(n8n_events(), "n8n")


def test_implementations_agree_on_the_content_hash(tmp_path):
    """The one field derived from meaning rather than from the moment.

    `content_hash` is computed from the event's content, so four
    implementations of the same scenario must agree on it, event by event.
    If one disagrees it is hashing something the others are not -- a
    cross-implementation defect the per-implementation checks cannot see.

    There is no exemption. The first version of this test exempted the n8n
    form's defaults (`triggered_by: "threshold"`, `recommended_due_days: 7`,
    `failure_confirmed: false`) as "what a form does". IAES_SPEC.md says
    otherwise: a producer MUST omit an optional field it was not given rather
    than substitute a value for it, and a default with a meaning is that
    substitution. The exemption was institutionalising the defect the battery
    exists to find. Only 05-custom has no hash: written by hand, on purpose.
    """
    produced = {
        "python": python_events(),
        "typescript": typescript_events(tmp_path),
        "node-red": nodered_events(),
        "n8n": n8n_events(),
    }
    reference = produced["python"]
    for name, events in produced.items():
        for got, ref in zip(events, reference):
            if "content_hash" not in ref:
                assert "content_hash" not in got, (
                    f"{name} / {ref['event_type']}: the hand-written custom event "
                    "carries a content_hash the reference does not"
                )
                continue
            assert got["data"] == ref["data"], (
                f"{name} / {ref['event_type']}: data differs from python's:\n"
                f"  {name}: {json.dumps(got['data'], sort_keys=True)}\n"
                f"  python: {json.dumps(ref['data'], sort_keys=True)}"
            )
            assert got.get("content_hash") == ref["content_hash"], (
                f"{name} / {ref['event_type']}: same data, different content_hash "
                f"({got.get('content_hash')} != {ref['content_hash']})"
            )


def test_the_custom_event_type_is_not_a_published_one():
    """Scenario 05 is only meaningful if the type really is unpublished."""
    # Derived from the schemas, which are what "published" means -- not from an
    # SDK constant. The TypeScript SDK exports PUBLISHED_EVENT_TYPES and the
    # Python one does not, and neither is required by surface.json, so a test
    # built on it would pass in one language and not exist in the other.
    published = {
        json.loads(p.read_text(encoding="utf-8"))["$id"].rsplit("/", 1)[-1]
        for p in (ROOT / "schema").glob("*.schema.json")
    }
    custom = [e for e in fixture()["events"] if e["scenario"] == "05-custom"][0]
    assert custom["event_type"] not in published, (
        "the custom scenario stopped proving anything: its event_type is now "
        "published, so accepting it no longer demonstrates that the catalog "
        "is open"
    )
