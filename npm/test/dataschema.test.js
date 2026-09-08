/**
 * v1.4 — every message carries the URI of its own contract.
 *
 * The field is derivable because the slug of every published schema IS its
 * event_type, so the producer gets it for free instead of being asked for it.
 */

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const {
  AssetMeasurement,
  AssetHealth,
  SPEC_VERSION,
  SCHEMA_BASE,
  schemaUriFor,
} = require("../dist/index.js");

describe("dataschema", () => {
  it("a published event type gets its schema URI", () => {
    const e = new AssetMeasurement({
      assetId: "MOTOR-001",
      measurementType: "vibration_velocity",
      value: 4.2,
      unit: "mm/s",
    }).toJSON();
    assert.equal(e.dataschema, "https://iaes.dev/schema/v2/asset.measurement");
    assert.equal(e.spec_version, "2.0");
  });

  it("the URI is the base plus the event type", () => {
    for (const t of ["asset.health", "sensor.registration", "maintenance.completion"]) {
      assert.equal(schemaUriFor(t), SCHEMA_BASE + t);
    }
  });

  it("an unpublished event type gets nothing", () => {
    // A URI that does not resolve is worse than an absent field. That was the
    // exact defect v1.4 corrected in the schemas themselves.
    assert.equal(schemaUriFor("vendor.custom_event"), undefined);
  });

  it("every published event type derives a URI that is not a guess", () => {
    // The envelope builder accepts an override, but it stays internal: the
    // Python side keeps its builder private too, and widening the public API
    // is a commitment, not a convenience. What is public is the derivation.
    const published = [
      "asset.measurement",
      "asset.health",
      "asset.hierarchy",
      "sensor.registration",
      "maintenance.work_order_intent",
      "maintenance.completion",
      "maintenance.spare_part_usage",
    ];
    for (const t of published) {
      const uri = schemaUriFor(t);
      assert.ok(uri, `${t} should derive a URI`);
      assert.ok(uri.startsWith("https://iaes.dev/schema/v2/"), "canonical base");
      assert.equal(uri.split("/").pop(), t, "the slug IS the event type");
    }
  });

  it("it is optional, so a consumer must not depend on it", () => {
    const e = new AssetHealth({
      assetId: "MOTOR-001",
      severity: "warning",
      description: "bearing",
    }).toJSON();
    delete e.dataschema;
    assert.equal(e.dataschema, undefined);
    assert.ok(e.event_type && e.spec_version, "the rest of the envelope still stands");
  });
});
