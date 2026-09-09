/**
 * The runtime half of the envelope-type fixes. The compile-time half is
 * `test/types/envelope-types.ts`, checked by `npm run typecheck`.
 *
 * `validate` now takes `unknown`, which is what a validator should take: it
 * must be able to receive something whose shape is not yet known to be valid.
 * Widening the parameter means it can also be handed things that are not
 * objects at all, so it has to reject those rather than crash reading
 * properties off them.
 */

const assert = require("node:assert/strict");
const test = require("node:test");

const {
  AssetMeasurement,
  validate,
  ValidationError,
} = require("../dist/index.js");

function envelope(extra = {}) {
  return {
    spec_version: "2.0",
    event_type: "asset.measurement",
    event_id: "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
    correlation_id: "3f2504e0-4f89-11d3-9a0c-0305e82c3302",
    timestamp: "2026-09-09T05:00:00Z",
    source: "sensor.line1",
    asset: { asset_id: "MOTOR-001" },
    data: { measurement_type: "vibration_velocity", value: 4.2, unit: "mm/s" },
    ...extra,
  };
}

// An envelope that arrives without content_hash: an IAESWireEnvelope in type
// terms. What the SDK BUILDS always has one -- see the last test -- and
// IAESEnvelope keeps the field required so code that reads it keeps compiling.
test("an envelope without content_hash is valid", () => {
  const event = envelope();
  assert.equal(event.content_hash, undefined);
  validate(event);
});

test("validate accepts what JSON.parse returns", () => {
  validate(JSON.parse(JSON.stringify(envelope())));
});

test("validate rejects what is not a JSON object instead of crashing", () => {
  for (const bad of [null, undefined, 42, "an event", [], true]) {
    assert.throws(
      () => validate(bad),
      ValidationError,
      `expected ValidationError for ${JSON.stringify(bad) ?? "undefined"}`,
    );
  }
});

test("the model classes still produce content_hash", () => {
  const event = new AssetMeasurement({
    asset_id: "MOTOR-001",
    source: "sensor.line1",
    measurement_type: "vibration_velocity",
    value: 4.2,
    unit: "mm/s",
  }).toJSON();
  assert.equal(typeof event.content_hash, "string");
  assert.equal(event.content_hash.length, 16);
  validate(event);
});
