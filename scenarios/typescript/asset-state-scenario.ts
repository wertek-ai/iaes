/**
 * The asset.state reference story, in TypeScript (IAES 2.1).
 *
 * A pump trips at 06:10. At 06:40 an inspection finds a bearing that needs
 * replacing, so the outage becomes corrective maintenance under a work order.
 * The pump is back in service, tested, at 10:40.
 *
 * `tests/test_asset_state_scenario.py` compiles and runs it, and checks the
 * output against `scenarios/fixture-asset-state.json` alongside the Python one.
 *
 * The timestamp is the fact: each event is stamped with the instant of the
 * transition, not the moment it is sent. And `toJSON()` returns an
 * `IAESWireEnvelope`, because asset.state carries no content_hash.
 */

import { writeFileSync } from "node:fs";
import {
  AssetState,
  DownCause,
  DownKind,
  UpDownState,
  UpMode,
  validate,
} from "@iaes/sdk";
import type { IAESWireEnvelope } from "@iaes/sdk";

const ASSET_ID = "PUMP-101";
const SOURCE = "plant.scada";

export function run(): IAESWireEnvelope[] {
  const trip = new AssetState({
    asset_id: ASSET_ID,
    source: SOURCE,
    timestamp: "2026-10-06T06:10:00Z",
    state: UpDownState.DOWN,
    down_kind: DownKind.UNPLANNED,
    down_cause: DownCause.OTHER_UNPLANNED, // a trip is an outage, not a failure
    previous_state: "up",
    detail: "trip",
    reason: "motor protection trip",
  }).toJSON();

  const corrective = new AssetState({
    asset_id: ASSET_ID,
    source: SOURCE,
    timestamp: "2026-10-06T06:40:00Z",
    state: UpDownState.DOWN, // down -> down: the cause changed, so it is a transition
    down_kind: DownKind.UNPLANNED,
    down_cause: DownCause.CORRECTIVE_MAINTENANCE,
    previous_state: "down",
    work_order_id: "WO-2026-1101",
    correlation_id: trip.correlation_id, // one down interval, one chain
    source_event_id: trip.event_id,
  }).toJSON();

  const back = new AssetState({
    asset_id: ASSET_ID,
    source: SOURCE,
    timestamp: "2026-10-06T10:40:00Z",
    state: UpDownState.UP,
    up_mode: UpMode.RUNNING,
    previous_state: "down",
    work_order_id: "WO-2026-1101",
    correlation_id: trip.correlation_id,
    source_event_id: corrective.event_id,
  }).toJSON();

  const events = [trip, corrective, back];
  for (const event of events) validate(event);
  return events;
}

declare const require: NodeRequire | undefined;
declare const module: NodeModule | undefined;
const isMain =
  typeof require !== "undefined" && typeof module !== "undefined"
    ? require.main === module
    : Boolean(process.argv[1]);

if (isMain) {
  const text = JSON.stringify(run(), null, 2);
  if (process.argv[2]) writeFileSync(process.argv[2], text, "utf-8");
  else console.log(text);
}
