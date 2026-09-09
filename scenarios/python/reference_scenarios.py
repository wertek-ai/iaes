#!/usr/bin/env python3
"""The reference scenarios, in Python.

One industrial story: a vibration model reads 4.2 mm/s RMS on a motor,
concludes the outer race of a bearing is degrading, asks maintenance to inspect
it, and a technician closes the loop. The same story is told in TypeScript, in
Node-RED and in n8n. **The workflow changes. The event meaning does not.**

Run it:

    python scenarios/python/reference_scenarios.py

`tests/test_reference_scenarios.py` runs it too, and checks the output against
`scenarios/fixture.json`.

### Why this platform?

Python is where IAES belongs when the producer IS the analysis: a model, a
notebook promoted to a service, a data pipeline, a backend that already holds
the reading and the conclusion. The event is constructed in the same process
that reached it, so there is no boundary to cross and nothing to serialise
twice.

Reach for Node-RED instead when the data arrives from a PLC or a broker, and
for n8n when the trigger is a webhook or a schedule. Neither is worse; they are
where the work already lives.
"""

import json
import sys
import uuid
from pathlib import Path

from iaes import (
    AssetHealth,
    AssetMeasurement,
    MaintenanceCompletion,
    WorkOrderIntent,
    validate,
)

ASSET = {
    "asset_id": "MOTOR-001",
    "asset_name": "Feed Pump Motor",
    "plant": "North Plant",
    "area": "Pumping",
}


def scenario_01_measurement() -> dict:
    """Emit a measurement. This is where the chain's correlation_id is born."""
    return AssetMeasurement(
        asset_id=ASSET["asset_id"],
        asset_name=ASSET["asset_name"],
        plant=ASSET["plant"],
        area=ASSET["area"],
        source="sensor.line1",
        measurement_type="vibration_velocity",
        value=4.2,
        unit="mm/s",
        units_qualifier="rms",
    ).to_dict()


def scenario_02_health(measurement: dict) -> dict:
    """A diagnosis about that measurement.

    `correlation_id` is carried forward and `source_event_id` points back, so a
    consumer can reconstruct the chain without knowing anything about the
    producers that made it.
    """
    return AssetHealth(
        asset_id=ASSET["asset_id"],
        asset_name=ASSET["asset_name"],
        plant=ASSET["plant"],
        area=ASSET["area"],
        source="acme.vibration",
        health_index=0.58,
        severity="high",
        failure_mode="bearing_outer_race",
        correlation_id=measurement["correlation_id"],
        source_event_id=measurement["event_id"],
    ).to_dict()


def scenario_03_work_order_intent(health: dict) -> dict:
    """A request to act. `priority` is the urgency of the RESPONSE.

    It is not `severity`, which is the condition of the asset. The two
    catalogues share the words low, medium and high and mean different things
    by them, and neither may be presented as the other.
    """
    return WorkOrderIntent(
        asset_id=ASSET["asset_id"],
        asset_name=ASSET["asset_name"],
        plant=ASSET["plant"],
        area=ASSET["area"],
        source="acme.rule_engine",
        title="Inspect drive-end bearing",
        priority="high",
        description=(
            "Vibration velocity at 4.2 mm/s RMS with an outer-race signature. "
            "Inspect the drive-end bearing at the next available window."
        ),
        correlation_id=health["correlation_id"],
        source_event_id=health["event_id"],
    ).to_dict()


def scenario_04_completion(intent: dict) -> dict:
    """The loop closes, still on the same correlation_id."""
    return MaintenanceCompletion(
        asset_id=ASSET["asset_id"],
        asset_name=ASSET["asset_name"],
        plant=ASSET["plant"],
        area=ASSET["area"],
        source="acme.cmms",
        work_order_id="WO-2026-0912",
        status="completed",
        correlation_id=intent["correlation_id"],
        source_event_id=intent["event_id"],
    ).to_dict()


def scenario_05_custom(measurement: dict) -> dict:
    """An event type IAES does not publish.

    There is no model class for it, and there does not need to be: the envelope
    is what interoperates. `validate()` checks the envelope and stops, because
    a type with no published schema has nothing to validate its payload
    against -- which is not a defect in the event.
    """
    return {
        "spec_version": measurement["spec_version"],
        "event_type": "acme.press_stroke",
        "event_id": str(uuid.uuid4()),
        "correlation_id": measurement["correlation_id"],
        "timestamp": measurement["timestamp"],
        "source": "acme.press_line",
        "asset": {"asset_id": ASSET["asset_id"]},
        "data": {"strokes": 412, "tonnage_peak": 88.4},
    }


def run() -> list:
    measurement = scenario_01_measurement()
    health = scenario_02_health(measurement)
    intent = scenario_03_work_order_intent(health)
    completion = scenario_04_completion(intent)
    custom = scenario_05_custom(measurement)

    events = [measurement, health, intent, completion, custom]
    for event in events:
        validate(event)          # scenario 02: validate an event
    return events


if __name__ == "__main__":
    events = run()
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    text = json.dumps(events, indent=2)
    if out:
        out.write_text(text, encoding="utf-8")
    else:
        print(text)
