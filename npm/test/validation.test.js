/**
 * Armed at zero: each test breaks an event on purpose and checks that
 * validation rejects it, and that the report names the offending field.
 *
 * The last two matter most. A validator that rejects a custom event_type
 * would contradict the specification, which permits one and tells consumers
 * they MUST NOT error on a type they do not recognise -- this repository has
 * made exactly that mistake before. And a validator that reports "invalid"
 * without a path satisfies nobody: the profile requires the path of the
 * offending field, because a message without one sends a reader looking.
 */

const test = require("node:test");
const assert = require("node:assert");

const { validate, ValidationError, loadSchema, loadEnvelopeSchema } = require("../dist/index.js");

function goodEvent(overrides = {}) {
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

test("a valid event passes", () => {
  validate(goodEvent());
});

test("a missing required field is rejected, and the path is named", () => {
  const event = goodEvent();
  delete event.asset;
  assert.throws(
    () => validate(event),
    (err) => {
      assert.ok(err instanceof ValidationError, "should be a ValidationError");
      assert.match(err.message, /asset/, "the report should name the field");
      assert.ok(err.errors.length > 0, "errors should be enumerated");
      return true;
    },
  );
});

test("a value outside the schema's range is rejected with its path", () => {
  const event = goodEvent({ data: { health_index: 42, severity: "medium" } });
  assert.throws(
    () => validate(event),
    (err) => {
      assert.ok(err instanceof ValidationError);
      assert.match(err.message, /health_index/, "the path locates the field");
      return true;
    },
  );
});

test("a value outside a closed catalog is rejected", () => {
  const event = goodEvent({ data: { health_index: 0.5, severity: "catastrophic" } });
  assert.throws(() => validate(event), ValidationError);
});

test("an event with no event_type is rejected", () => {
  const event = goodEvent();
  delete event.event_type;
  assert.throws(() => validate(event), ValidationError);
});

test("a custom event_type is NOT an invalid event", () => {
  // The specification permits a producer to emit its own type in a namespace
  // it controls, omitting dataschema. The envelope still applies; the payload
  // has nothing to be judged against. GOVERNANCE.md 9.1 says so in the
  // definition of wire conformance.
  validate(goodEvent({ event_type: "acme.press_stroke", data: { strokes: 12 } }));
});

test("a custom event_type with a broken envelope is still rejected", () => {
  // Otherwise "unknown type" would be a way to skip validation entirely.
  const event = goodEvent({ event_type: "acme.press_stroke", data: { strokes: 12 } });
  delete event.source;
  assert.throws(
    () => validate(event),
    (err) => {
      assert.ok(err instanceof ValidationError);
      assert.match(err.message, /source/);
      return true;
    },
  );
});

test("every published event type has a loadable schema", () => {
  const { PUBLISHED_EVENT_TYPES } = require("../dist/index.js");
  for (const type of PUBLISHED_EVENT_TYPES) {
    const schema = loadSchema(type);
    assert.equal(schema.$id, `https://iaes.dev/schema/v2/${type}`);
  }
  assert.ok(loadEnvelopeSchema().$id, "the envelope schema loads");
});

test("format is not asserted, and the two SDKs agree that it is not", () => {
  // Draft 2020-12 makes `format` an annotation. Both SDKs accept a malformed
  // timestamp, and that agreement is the point: an SDK that asserted `format`
  // would reject events the other accepts, so "stricter" would mean "wrong"
  // for anyone moving between them.
  //
  // Pinned deliberately rather than left to whoever next adds ajv-formats.
  // Making `format` binding is a narrowing change under GOVERNANCE.md 4.2 and
  // needs its own memo; until then this is the behaviour, and it is checked.
  validate(goodEvent({ timestamp: "banana" }));
});
