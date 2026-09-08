/**
 * A fault in the SDK must not become permissiveness in the contract.
 *
 * An earlier version of validate() wrapped loadSchema in a bare `catch` and
 * treated anything that threw as "this type has no published schema". So a
 * missing file, corrupt JSON or an unreadable disk would have degraded a
 * PUBLISHED type to envelope-only validation — and every asset.health payload
 * would have passed, however invalid, because the schema that judges it failed
 * to load.
 *
 * This file lives on its own because it mocks `fs` before the SDK is required:
 * `readSchema` caches by filename, so a test that ran after any other would be
 * served from the cache and never reach the mock. Node runs each test file in
 * its own process, which gives it a clean module registry.
 */

const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");

const realReadFileSync = fs.readFileSync;

// Fail exactly one published schema, and only that one.
fs.readFileSync = function (target, ...rest) {
  if (String(target).includes("asset-health.schema.json")) {
    throw new Error("EIO: simulated read failure");
  }
  return realReadFileSync.call(this, target, ...rest);
};

const { validate, ValidationError } = require("../dist/index.js");

function healthEvent(overrides = {}) {
  return {
    spec_version: "2.0",
    event_type: "asset.health",
    event_id: "550e8400-e29b-41d4-a716-446655440000",
    correlation_id: "550e8400-e29b-41d4-a716-446655440000",
    timestamp: "2026-09-08T12:00:00Z",
    source: "acme.diagnostics",
    asset: { asset_id: "MOTOR-001" },
    data: { health_index: 0.82, severity: "medium" },
    ...overrides,
  };
}

test("a schema that fails to load does NOT fall back to envelope-only", () => {
  // The payload here is invalid against asset.health: health_index is out of
  // range and severity is not in the catalog. Envelope-only validation would
  // accept it, because the envelope says nothing about `data`.
  const invalidPayload = healthEvent({
    data: { health_index: 42, severity: "catastrophic" },
  });

  assert.throws(
    () => validate(invalidPayload),
    (err) => {
      assert.ok(
        !(err instanceof ValidationError),
        "a read failure is not a validation failure: it must surface as itself",
      );
      assert.match(err.message, /simulated read failure/);
      return true;
    },
    "the load failure must propagate, not silently widen what is accepted",
  );
});

test("and a valid payload of that type does not pass either", () => {
  // The stronger half: not even a well-formed event slips through. If it did,
  // the failure would be invisible until the day an invalid one arrived.
  assert.throws(() => validate(healthEvent()), /simulated read failure/);
});

test("a genuinely custom event_type still takes the envelope-only path", () => {
  // The fix must not close the door it was meant to leave open: a type with no
  // published schema is decided by membership, and never reaches a file read.
  validate(healthEvent({ event_type: "acme.press_stroke", data: { strokes: 12 } }));
});

test.after(() => {
  fs.readFileSync = realReadFileSync;
});
