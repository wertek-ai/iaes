#!/usr/bin/env python3
"""The asset.state reference story, in Python (IAES 2.1).

A pump trips at 06:10. At 06:40 an inspection finds a bearing that needs
replacing, so the outage becomes corrective maintenance under a work order. The
pump is back in service, tested, at 10:40.

Run it:

    python scenarios/python/asset_state_scenario.py

`tests/test_asset_state_scenario.py` runs it too, and checks the output against
`scenarios/fixture-asset-state.json`.

Two things this story shows that the first one does not:

- **The timestamp is the fact.** Each event is stamped with the instant of the
  transition, not the moment it is sent. A producer that leaves the default
  (now) emits a valid event and a wrong down interval.
- **No content_hash.** Two identical trips would hash the same, so the type
  carries none and consumers deduplicate it by event_id.
"""

import json
from datetime import datetime, timezone

from iaes import AssetState, DownCause, DownKind, UpDownState, UpMode, validate

ASSET_ID = "PUMP-101"
SOURCE = "plant.scada"


def at(hour: int, minute: int) -> datetime:
    return datetime(2026, 10, 6, hour, minute, tzinfo=timezone.utc)


def run() -> list:
    trip = AssetState(
        asset_id=ASSET_ID,
        source=SOURCE,
        timestamp=at(6, 10),
        state=UpDownState.DOWN,
        down_kind=DownKind.UNPLANNED,
        down_cause=DownCause.OTHER_UNPLANNED,  # a trip is an outage, not a failure
        previous_state="up",
        detail="trip",
        reason="motor protection trip",
    ).to_dict()

    corrective = AssetState(
        asset_id=ASSET_ID,
        source=SOURCE,
        timestamp=at(6, 40),
        state=UpDownState.DOWN,  # down -> down: the cause changed, so it is a transition
        down_kind=DownKind.UNPLANNED,
        down_cause=DownCause.CORRECTIVE_MAINTENANCE,
        previous_state="down",
        work_order_id="WO-2026-1101",
        correlation_id=trip["correlation_id"],  # one down interval, one chain
        source_event_id=trip["event_id"],
    ).to_dict()

    back = AssetState(
        asset_id=ASSET_ID,
        source=SOURCE,
        timestamp=at(10, 40),
        state=UpDownState.UP,
        up_mode=UpMode.RUNNING,
        previous_state="down",
        work_order_id="WO-2026-1101",
        correlation_id=trip["correlation_id"],
        source_event_id=corrective["event_id"],
    ).to_dict()

    events = [trip, corrective, back]
    for event in events:
        validate(event)
    return events


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
