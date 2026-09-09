/**
 * Type-level tests. The compiler is the assertion; `npm run typecheck` runs it.
 *
 * The package's other tests are JavaScript, so nothing checked the SHAPE of
 * what the SDK exports. Two defects lived behind that, and the reference
 * scenarios found them by doing what an integrator does first:
 *
 *   - `IAESEnvelope` declared `content_hash: string` while
 *     `iaes-envelope.schema.json` does not list it in `required`, so a
 *     hand-written envelope that conforms did not compile.
 *   - `validate` took `Record<string, unknown>`, which `IAESEnvelope` does not
 *     satisfy -- it has no index signature -- so handing the SDK's own type
 *     back to the SDK needed a cast.
 *
 * A cast would have hidden both. That is why these are compile-time checks and
 * not runtime ones: the failure they guard against is a failure to compile.
 */

import { AssetMeasurement, validate } from "../../src/index.js";
import type { IAESEnvelope } from "../../src/index.js";

// 1. A hand-written envelope without content_hash compiles.
const handWritten: IAESEnvelope = {
  spec_version: "2.0",
  event_type: "acme.press_stroke",
  event_id: "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
  correlation_id: "3f2504e0-4f89-11d3-9a0c-0305e82c3302",
  timestamp: "2026-09-09T05:00:00Z",
  source: "acme.press_line",
  asset: { asset_id: "PRESS-01" },
  data: { strokes: 412 },
};

// 2. validate accepts the SDK's own envelope, with no cast.
validate(handWritten);

const built = new AssetMeasurement({
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

// 4. content_hash is still declared -- optional, not absent.
const hash: string | undefined = built.content_hash;

export { handWritten, hash };
