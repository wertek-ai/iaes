/**
 * The reference scenarios, in TypeScript.
 *
 * One industrial story: a vibration model reads 4.2 mm/s RMS on a motor,
 * concludes the outer race of a bearing is degrading, asks maintenance to
 * inspect it, and a technician closes the loop. The same story is told in
 * Python, in Node-RED and in n8n.
 * **The workflow changes. The event meaning does not.**
 *
 * Run it:
 *
 *     npx tsx scenarios/typescript/reference-scenarios.ts
 *
 * `tests/test_reference_scenarios.py` runs it too, and checks the output
 * against `scenarios/fixture.json` alongside the Python one.
 *
 * ### Why this platform?
 *
 * TypeScript is where IAES belongs when the producer is a SERVICE: an API that
 * already receives the reading, an edge process on a gateway, a worker in a
 * queue, anything that will be deployed as running software rather than
 * invoked as a script. The types come with the SDK, so a malformed event is a
 * compile error rather than a validation failure in production.
 *
 * Reach for Python when the producer IS the model, for Node-RED at the OT
 * boundary, and for n8n when the trigger is a webhook or a schedule.
 */

import { randomUUID } from "node:crypto";
import { writeFileSync } from "node:fs";
import {
  AssetHealth,
  AssetMeasurement,
  MaintenanceCompletion,
  WorkOrderIntent,
  validate,
} from "@iaes/sdk";
import type { IAESEnvelope, IAESWireEnvelope } from "@iaes/sdk";

const ASSET = {
  asset_id: "MOTOR-001",
  asset_name: "Feed Pump Motor",
  plant: "North Plant",
  area: "Pumping",
};

/** Emit a measurement. This is where the chain's correlation_id is born. */
function scenario01Measurement(): IAESEnvelope {
  return new AssetMeasurement({
    asset_id: ASSET.asset_id,
    asset_name: ASSET.asset_name,
    plant: ASSET.plant,
    area: ASSET.area,
    source: "sensor.line1",
    measurement_type: "vibration_velocity",
    value: 4.2,
    unit: "mm/s",
    units_qualifier: "rms",
  }).toJSON();
}

/**
 * A diagnosis about that measurement. `correlation_id` is carried forward and
 * `source_event_id` points back, so a consumer can reconstruct the chain
 * without knowing anything about the producers that made it.
 */
function scenario02Health(measurement: any): IAESEnvelope {
  return new AssetHealth({
    asset_id: ASSET.asset_id,
    asset_name: ASSET.asset_name,
    plant: ASSET.plant,
    area: ASSET.area,
    source: "acme.vibration",
    health_index: 0.58,
    severity: "high",
    failure_mode: "bearing_outer_race",
    correlation_id: measurement.correlation_id,
    source_event_id: measurement.event_id,
  }).toJSON();
}

/**
 * A request to act. `priority` is the urgency of the RESPONSE; it is not
 * `severity`, which is the condition of the asset. The two catalogues share
 * the words low, medium and high and mean different things by them.
 */
function scenario03WorkOrderIntent(health: any): IAESEnvelope {
  return new WorkOrderIntent({
    asset_id: ASSET.asset_id,
    asset_name: ASSET.asset_name,
    plant: ASSET.plant,
    area: ASSET.area,
    source: "acme.rule_engine",
    title: "Inspect drive-end bearing",
    priority: "high",
    description:
      "Vibration velocity at 4.2 mm/s RMS with an outer-race signature. " +
      "Inspect the drive-end bearing at the next available window.",
    correlation_id: health.correlation_id,
    source_event_id: health.event_id,
  }).toJSON();
}

/** The loop closes, still on the same correlation_id. */
function scenario04Completion(intent: any): IAESEnvelope {
  return new MaintenanceCompletion({
    asset_id: ASSET.asset_id,
    asset_name: ASSET.asset_name,
    plant: ASSET.plant,
    area: ASSET.area,
    source: "acme.cmms",
    work_order_id: "WO-2026-0912",
    status: "completed",
    correlation_id: intent.correlation_id,
    source_event_id: intent.event_id,
  }).toJSON();
}

/**
 * An event type IAES does not publish. There is no model class for it, and
 * there does not need to be: the envelope is what interoperates. `validate()`
 * checks the envelope and stops, because a type with no published schema has
 * nothing to validate its payload against -- which is not a defect in the
 * event.
 *
 * Its return type is `IAESWireEnvelope`, not `IAESEnvelope`, and the compiler
 * insists: `IAESEnvelope` describes what this SDK PRODUCES, and everything it
 * produces carries a `content_hash`. This event was written by hand and does
 * not. Both conform -- the schema does not require the field -- and the two
 * types are what keeps that true without breaking code that reads the hash off
 * an event the SDK built.
 */
function scenario05Custom(measurement: any): IAESWireEnvelope {
  return {
    spec_version: measurement.spec_version,
    event_type: "acme.press_stroke",
    event_id: randomUUID(),
    correlation_id: measurement.correlation_id,
    timestamp: measurement.timestamp,
    source: "acme.press_line",
    asset: { asset_id: ASSET.asset_id },
    data: { strokes: 412, tonnage_peak: 88.4 },
  };
}

export function run(): IAESWireEnvelope[] {
  const measurement = scenario01Measurement();
  const health = scenario02Health(measurement);
  const intent = scenario03WorkOrderIntent(health);
  const completion = scenario04Completion(intent);
  const custom = scenario05Custom(measurement);

  const events = [measurement, health, intent, completion, custom];
  for (const event of events) validate(event); // scenario 02: validate an event
  return events;
}

// Print when run directly, stay quiet when imported. Compares the module
// against the entry point rather than matching the FILENAME: the compiled
// output is not called reference-scenarios.js, so a name check silently did
// nothing -- the file compiled, ran, and printed no events.
declare const require: NodeRequire | undefined;
declare const module: NodeModule | undefined;
const isMain =
  typeof require !== "undefined" && typeof module !== "undefined"
    ? require.main === module
    : Boolean(process.argv[1]);

if (isMain) {
  const events = run();
  const text = JSON.stringify(events, null, 2);
  if (process.argv[2]) writeFileSync(process.argv[2], text, "utf-8");
  else console.log(text);
}
