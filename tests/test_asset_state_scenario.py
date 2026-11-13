"""The asset.state story, told by the two SDKs, produces the same facts.

`scenarios/fixture-asset-state.json` is the trip of IAES-RFC-010's worked
example: down at 06:10 (a trip), still down at 06:40 but now corrective
maintenance under a work order, up at 10:40. Both SDKs tell it and both are
checked against the fixture here.

What differs from the first battery (`tests/test_reference_scenarios.py`):

- **Timestamps are compared.** For this type the timestamp is the instant of
  the transition, the fact a consumer computes a down interval from. Compared
  as instants, not as strings: Python writes `+00:00`, TypeScript keeps the
  `Z` it was given, and both are RFC 3339 UTC.
- **No content_hash, anywhere.** Its absence is the property, so it is checked
  on every event rather than assumed.
- **Two identical trips are two events.** Built twice from the same data, the
  SDK must not give a consumer anything to merge them by except event_id.
"""

import json
from datetime import datetime
from pathlib import Path

from tests.test_reference_scenarios import ROOT, typescript_events

FIXTURE = ROOT / "scenarios" / "fixture-asset-state.json"
TS_SCENARIO = ROOT / "scenarios" / "typescript" / "asset-state-scenario.ts"


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def python_events() -> list:
    import sys

    sys.path.insert(0, str(ROOT / "scenarios" / "python"))
    sys.path.insert(0, str(ROOT / "src"))
    import asset_state_scenario

    return asset_state_scenario.run()


def check(events: list, language: str) -> None:
    fx = fixture()
    expected = fx["events"]
    assert len(events) == len(expected), f"{language}: {len(events)} events, fixture has {len(expected)}"

    for got, want in zip(events, expected):
        where = f"{language} / {want['scenario']}"
        assert got["event_type"] == want["event_type"], where
        assert got["spec_version"] == fx["spec_version"], where
        assert got["source"] == want["source"], where
        assert got["asset"]["asset_id"] == fx["asset"]["asset_id"], where
        assert got["data"] == want["data"], f"{where}: data"
        assert instant(got["timestamp"]) == instant(want["timestamp"]), (
            f"{where}: the timestamp is the instant of the transition, "
            f"{got['timestamp']} != {want['timestamp']}")
        assert instant(got["timestamp"]).utcoffset().total_seconds() == 0, f"{where}: UTC"
        assert "content_hash" not in got, f"{where}: asset.state carries no content_hash"

    # One down interval, one chain.
    assert len({e["correlation_id"] for e in events}) == 1, f"{language}: one chain"
    by_scenario = dict(zip([e["scenario"] for e in expected], events))
    for want, got in zip(expected, events):
        if "follows" in want:
            assert got.get("source_event_id") == by_scenario[want["follows"]]["event_id"], (
                f"{language} / {want['scenario']} must point back at {want['follows']}")
    ids = [e["event_id"] for e in events]
    assert len(set(ids)) == len(ids), f"{language}: event_id must be unique"


def test_python_tells_the_trip():
    check(python_events(), "python")


def test_typescript_tells_the_trip(tmp_path):
    check(typescript_events(tmp_path, TS_SCENARIO), "typescript")


def test_two_identical_trips_are_two_events():
    """IAES_SPEC.md, asset.state, rule 3. A hash over data would make them one."""
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from iaes import AssetState

    trip = dict(asset_id="PUMP-101", source="plant.scada", state="down",
                down_kind="unplanned", down_cause="other_unplanned", detail="trip")
    first = AssetState(**trip, timestamp="2026-10-06T06:10:00Z").to_dict()
    second = AssetState(**trip, timestamp="2026-10-07T06:10:00Z").to_dict()
    assert first["data"] == second["data"]
    assert "content_hash" not in first and "content_hash" not in second
    assert first["event_id"] != second["event_id"]


def test_the_fixture_is_a_published_type_and_valid():
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from iaes import validate

    fx = fixture()
    assert (ROOT / "schema" / "asset-state.schema.json").exists()
    for want in fx["events"]:
        validate({
            "spec_version": fx["spec_version"], "event_type": want["event_type"],
            "event_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "correlation_id": "9b2a3f4e-1c5d-4e6f-8a7b-0c1d2e3f4a5b",
            "timestamp": want["timestamp"], "source": want["source"],
            "asset": dict(fx["asset"]), "data": dict(want["data"]),
        })
