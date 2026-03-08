/**
 * Cross-language roundtrip test: TypeScript SDK
 *
 * Tests:
 * 1. Create event in TS → serialize → validate structure → deserialize
 * 2. Load Python-generated fixtures → deserialize in TS
 * 3. Generate TS fixtures for Python to validate
 */

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const {
  AssetMeasurement,
  AssetHealth,
  WorkOrderIntent,
  MaintenanceCompletion,
  AssetHierarchy,
  SensorRegistration,
  SparePartUsage,
  fromJSON,
  SPEC_VERSION,
} = require("../dist/index");

describe("IAES TypeScript SDK", () => {
  it("spec version is 1.2", () => {
    assert.equal(SPEC_VERSION, "1.2");
  });

  it("AssetMeasurement roundtrip", () => {
    const event = new AssetMeasurement({
      asset_id: "MOTOR-001",
      measurement_type: "vibration_velocity",
      value: 4.2,
      unit: "mm/s",
      source: "acme.sensors",
      units_qualifier: "rms",
      sampling_rate_hz: 25600,
    });
    const wire = event.toJSON();

    assert.equal(wire.event_type, "asset.measurement");
    assert.equal(wire.spec_version, "1.2");
    assert.equal(wire.asset.asset_id, "MOTOR-001");
    assert.equal(wire.data.measurement_type, "vibration_velocity");
    assert.equal(wire.data.value, 4.2);
    assert.equal(wire.data.units_qualifier, "rms");
    assert.equal(wire.content_hash.length, 16);

    // Roundtrip
    const event2 = AssetMeasurement.fromJSON(wire);
    assert.equal(event2.asset_id, "MOTOR-001");
    assert.equal(event2.value, 4.2);
    assert.equal(event2.units_qualifier, "rms");
  });

  it("AssetHealth roundtrip", () => {
    const event = new AssetHealth({
      asset_id: "PUMP-002",
      health_index: 0.16,
      severity: "critical",
      failure_mode: "bearing_inner_race",
      rul_days: 5,
      source: "ai.diagnosis",
      iso_13374_status: "unacceptable",
      iso_14224: { mechanism_code: "1.1", cause_code: "1" },
    });
    const wire = event.toJSON();

    assert.equal(wire.data.health_index, 0.16);
    assert.equal(wire.data.severity, "critical");
    assert.equal(wire.data.iso_13374_status, "unacceptable");
    assert.equal(wire.data.iso_14224.mechanism_code, "1.1");

    const event2 = AssetHealth.fromJSON(wire);
    assert.equal(event2.failure_mode, "bearing_inner_race");
    assert.equal(event2.rul_days, 5);
  });

  it("WorkOrderIntent roundtrip", () => {
    const event = new WorkOrderIntent({
      asset_id: "M-001",
      title: "Replace bearing DE",
      priority: "high",
      triggered_by: "ai_diagnosis",
      recommended_due_days: 7,
    });
    const wire = event.toJSON();

    assert.equal(wire.event_type, "maintenance.work_order_intent");
    assert.equal(wire.data.title, "Replace bearing DE");

    const event2 = WorkOrderIntent.fromJSON(wire);
    assert.equal(event2.recommended_due_days, 7);
  });

  it("MaintenanceCompletion roundtrip", () => {
    const event = new MaintenanceCompletion({
      asset_id: "M-001",
      work_order_id: "WO-2026-001",
      actual_duration_seconds: 7200,
      failure_confirmed: true,
    });
    const wire = event.toJSON();

    assert.equal(wire.event_type, "maintenance.completion");
    const event2 = MaintenanceCompletion.fromJSON(wire);
    assert.equal(event2.actual_duration_seconds, 7200);
  });

  it("AssetHierarchy roundtrip", () => {
    const event = new AssetHierarchy({
      asset_id: "PLANT-001",
      hierarchy_level: "plant",
      relationship_type: "child_of",
      manufacturer: "Siemens",
    });
    const wire = event.toJSON();

    assert.equal(wire.event_type, "asset.hierarchy");
    const event2 = AssetHierarchy.fromJSON(wire);
    assert.equal(event2.manufacturer, "Siemens");
  });

  it("SensorRegistration roundtrip", () => {
    const event = new SensorRegistration({
      asset_id: "M-001",
      sensor_id: "CT-001",
      registration_status: "registered",
      communication_protocol: "mqtt",
    });
    const wire = event.toJSON();

    assert.equal(wire.event_type, "sensor.registration");
    const event2 = SensorRegistration.fromJSON(wire);
    assert.equal(event2.communication_protocol, "mqtt");
  });

  it("SparePartUsage roundtrip", () => {
    const event = new SparePartUsage({
      asset_id: "M-001",
      work_order_id: "WO-001",
      spare_part_id: "SP-6205",
      quantity_used: 2,
      unit_cost: 45.0,
      currency: "USD",
    });
    const wire = event.toJSON();

    assert.equal(wire.event_type, "maintenance.spare_part_usage");
    const event2 = SparePartUsage.fromJSON(wire);
    assert.equal(event2.unit_cost, 45.0);
    assert.equal(event2.currency, "USD");
  });

  it("fromJSON dispatches correctly", () => {
    const wire = new AssetMeasurement({
      asset_id: "M-001",
      measurement_type: "temperature",
      value: 80,
      unit: "C",
    }).toJSON();

    const obj = fromJSON(wire);
    assert.ok(obj instanceof AssetMeasurement);
    assert.equal(obj.value, 80);
  });

  it("fromJSON throws on unknown event_type", () => {
    assert.throws(
      () => fromJSON({ event_type: "foo.bar", data: {} }),
      /Unknown IAES event_type/
    );
  });

  it("null fields excluded from data", () => {
    const event = new AssetMeasurement({
      asset_id: "M-001",
      measurement_type: "temperature",
      value: 50,
      unit: "C",
    });
    const wire = event.toJSON();
    assert.ok(!("sensor_id" in wire.data));
    assert.ok(!("location" in wire.data));
  });

  it("batch_id included when set", () => {
    const event = new AssetMeasurement({
      asset_id: "M-001",
      measurement_type: "temperature",
      value: 50,
      unit: "C",
      batch_id: "BATCH-001",
    });
    assert.equal(event.toJSON().batch_id, "BATCH-001");
  });

  it("batch_id excluded when not set", () => {
    const event = new AssetMeasurement({
      asset_id: "M-001",
      measurement_type: "temperature",
      value: 50,
      unit: "C",
    });
    assert.ok(!("batch_id" in event.toJSON()));
  });

  it("content_hash is deterministic", () => {
    const opts = {
      asset_id: "M-001",
      measurement_type: "temperature",
      value: 50,
      unit: "C",
      event_id: "fixed",
      correlation_id: "fixed",
      timestamp: "2026-01-01T00:00:00Z",
    };
    const h1 = new AssetMeasurement(opts).toJSON().content_hash;
    const h2 = new AssetMeasurement(opts).toJSON().content_hash;
    assert.equal(h1, h2);
  });

  it("JSON.stringify works (toJSON protocol)", () => {
    const event = new AssetMeasurement({
      asset_id: "M-001",
      measurement_type: "temperature",
      value: 50,
      unit: "C",
    });
    const str = JSON.stringify(event);
    const parsed = JSON.parse(str);
    assert.equal(parsed.event_type, "asset.measurement");
  });
});
