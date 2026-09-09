/**
 * Type-level tests. The compiler is the assertion; `npm run typecheck` runs it.
 *
 * The package's other tests are JavaScript, so nothing checked the SHAPE of
 * what the SDK exports. The reference scenarios found two defects by doing
 * what an integrator does first, and a third arrived with the first fix.
 *
 *   - `validate` took `Record<string, unknown>`, which `IAESEnvelope` does not
 *     satisfy -- it has no index signature -- so handing the SDK's own type
 *     back to the SDK needed a cast.
 *   - `IAESEnvelope` had no way to describe an envelope that omits
 *     `content_hash`, which the schema permits, so a conforming hand-written
 *     event did not compile.
 *   - And the first attempt at that second fix made `content_hash` optional on
 *     `IAESEnvelope` itself. Measured with a positive control: the same code
 *     compiles with the field required and fails with it optional, so
 *     `event.content_hash.slice(0, 8)` -- valid in 2.0.0, on a field the SDK
 *     always sets -- became an error in a PATCH release. GOVERNANCE.md 3.1
 *     forbids that. The two contracts are two types now.
 *
 * A cast would have hidden all three. That is why these are compile-time
 * checks: the failure they guard against is a failure to compile.
 */

import { AssetMeasurement, validate } from "../../src/index.js";
import type { IAESEnvelope, IAESWireEnvelope } from "../../src/index.js";

// 1. An envelope as it may ARRIVE: conforming, and without content_hash.
const handWritten: IAESWireEnvelope = {
  spec_version: "2.0",
  event_type: "acme.press_stroke",
  event_id: "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
  correlation_id: "3f2504e0-4f89-11d3-9a0c-0305e82c3302",
  timestamp: "2026-09-09T05:00:00Z",
  source: "acme.press_line",
  asset: { asset_id: "PRESS-01" },
  data: { strokes: 412 },
};

// 2. validate accepts it, and the SDK's own type, with no cast.
validate(handWritten);

const built: IAESEnvelope = new AssetMeasurement({
  asset_id: "MOTOR-001",
  source: "sensor.line1",
  measurement_type: "vibration_velocity",
  value: 4.2,
  unit: "mm/s",
}).toJSON();
validate(built);

// 3. And whatever JSON.parse returns, which is `any` at the boundary and
//    `unknown` in any codebase that has turned that off.
const parsed: unknown = JSON.parse("{}");
validate(parsed);

// 4. COMPATIBILITY CONTROL. This is the line that 2.0.0 allowed and that a
//    weakened IAESEnvelope would break. `string`, not `string | undefined`,
//    and no optional chaining: if this ever needs a `?.` or a `!`, the patch
//    release broke somebody's code.
const hash: string = built.content_hash;
const eight: string = built.content_hash.slice(0, 8);

// 5. An envelope the SDK produced is also a valid wire envelope. The other
//    direction must NOT hold, and is checked with @ts-expect-error: a wire
//    envelope may lack the hash, so it cannot stand in for one that has it.
const asWire: IAESWireEnvelope = built;
// @ts-expect-error a wire envelope may omit content_hash
const asProduced: IAESEnvelope = handWritten;

// 6. source_event_id may be explicitly null on the wire, because the IAES 2.0
//    schema permits it. The specification says the field references the
//    originating event and assigns no meaning to null; a consumer still has to
//    be able to type what it receives.
const incoming: IAESWireEnvelope = {
  spec_version: "2.0",
  event_type: "asset.measurement",
  event_id: "3f2504e0-4f89-11d3-9a0c-0305e82c3303",
  correlation_id: "3f2504e0-4f89-11d3-9a0c-0305e82c3304",
  timestamp: "2026-09-09T05:00:00Z",
  source: "sensor.line1",
  source_event_id: null,
  asset: { asset_id: "MOTOR-001" },
  data: { measurement_type: "vibration_velocity", value: 4.2, unit: "mm/s" },
};
validate(incoming);

// 7. And the PRODUCED type is not weakened while relaxing the wire one. This
//    SDK never emits null, so `string | undefined` is the whole domain, and a
//    consumer that already narrowed on it keeps compiling.
const produced: IAESEnvelope = built;
const sourceEventId: string | undefined = produced.source_event_id;

export {
  handWritten,
  built,
  hash,
  eight,
  asWire,
  asProduced,
  incoming,
  sourceEventId,
};
