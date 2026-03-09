const { describe, it } = require("node:test");
const assert = require("node:assert/strict");

// --- Mock RED ---

function createMockRED() {
  const types = {};
  return {
    nodes: {
      createNode(node, config) {
        node.config = config;
        node._handlers = {};
        node.on = (event, fn) => { node._handlers[event] = fn; };
        node.warn = (msg) => { node._warnings = node._warnings || []; node._warnings.push(msg); };
        node.error = (err, msg) => { node._errors = node._errors || []; node._errors.push({ err, msg }); };
        node.send = (msg) => { node._sent = node._sent || []; node._sent.push(msg); };
      },
      registerType(name, constructor) {
        types[name] = constructor;
      },
    },
    util: {
      cloneMessage(msg) { return JSON.parse(JSON.stringify(msg)); },
    },
    types,
  };
}

function createNode(RED, typeName, config) {
  const Constructor = RED.types[typeName];
  const node = {};
  Constructor.call(node, config);
  return node;
}

// Sparkplug node calls send([msg, null]) for success, send([null, msg]) for errors.
// outputs[] = array of send() calls. Each is what was passed: [port0_msg, port1_msg]
function sendInput(node, msg) {
  const outputs = [];
  const send = function (out) { outputs.push(out); };
  const errors = [];
  const done = function (err) { if (err) errors.push(err); };
  node._handlers.input(msg, send, done);
  return { outputs, errors };
}

// --- Load the node ---

const RED = createMockRED();
require("../nodes/iaes-sparkplug.js")(RED);

// --- Tests ---

describe("iaes-sparkplug node", () => {

  describe("topic parsing", () => {
    it("should extract device_id from Sparkplug DDATA topic", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/PlantA/DDATA/EdgeNode1/Motor001",
        payload: {
          metrics: [{ name: "Temperature", value: 72.5 }],
        },
      });

      // per_metric: one send([msg, null]) per metric
      const iaes = outputs[0][0].payload;
      assert.equal(iaes.asset.asset_id, "Motor001");
      assert.equal(iaes.data.measurement_type, "temperature");
      assert.equal(iaes.data.value, 72.5);
    });

    it("should use edge_node_id when configured", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "edge_node",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/PlantA/DDATA/GW-100/Sensor42",
        payload: { metrics: [{ name: "Temperature", value: 25 }] },
      });

      assert.equal(outputs[0][0].payload.asset.asset_id, "GW-100");
    });

    it("should use custom asset_id when configured", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "custom",
        customAssetId: "PUMP-042",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/PlantA/DDATA/Edge1/Dev1",
        payload: { metrics: [{ name: "Pressure", value: 3.5 }] },
      });

      assert.equal(outputs[0][0].payload.asset.asset_id, "PUMP-042");
    });

    it("should handle NDATA topic (no device_id)", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/PlantA/NDATA/EdgeNode1",
        payload: { metrics: [{ name: "Temperature", value: 50 }] },
      });

      // Falls back to edge_node_id when no device_id in topic
      assert.equal(outputs[0][0].payload.asset.asset_id, "EdgeNode1");
    });
  });

  describe("metric type inference", () => {
    const testCases = [
      { name: "Temperature", expected: "temperature" },
      { name: "Temp", expected: "temperature" },
      { name: "Vibration/Velocity", expected: "vibration_velocity" },
      { name: "Vibration_Acceleration", expected: "vibration_acceleration" },
      { name: "Motor Current", expected: "current" },
      { name: "Bus Voltage", expected: "voltage" },
      { name: "Active Power", expected: "power" },
      { name: "Power Factor", expected: "power_factor" },
      { name: "PF", expected: "power_factor" },
      { name: "THD_Voltage", expected: "thd_voltage" },
      { name: "Speed RPM", expected: "speed" },
      { name: "Bearing Pressure", expected: "pressure" },
      { name: "Coolant Flow", expected: "flow" },
      { name: "UnknownMetric123", expected: "custom" },
    ];

    for (const tc of testCases) {
      it(`should map "${tc.name}" to "${tc.expected}"`, () => {
        const node = createNode(RED, "iaes-sparkplug", {
          assetIdSource: "device_id",
          outputMode: "per_metric",
        });

        const { outputs } = sendInput(node, {
          topic: "spBv1.0/G/DDATA/E/D",
          payload: { metrics: [{ name: tc.name, value: 1.0 }] },
        });

        assert.equal(outputs[0][0].payload.data.measurement_type, tc.expected);
      });
    }
  });

  describe("metric filtering", () => {
    it("should filter metrics by regex", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "batch",
        metricFilter: "^(Temperature|Vibration)",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: {
          metrics: [
            { name: "Temperature", value: 72 },
            { name: "Vibration/Velocity", value: 4.2 },
            { name: "Status Code", value: 1 },
            { name: "Uptime Hours", value: 1200 },
          ],
        },
      });

      // batch: send([msg, null]) once, msg.payload = array
      const events = outputs[0][0].payload;
      assert.equal(events.length, 2);
      assert.equal(events[0].data.measurement_type, "temperature");
      assert.equal(events[1].data.measurement_type, "vibration_velocity");
    });

    it("should pass all metrics when no filter is set", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "batch",
        metricFilter: "",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: {
          metrics: [
            { name: "Temperature", value: 72 },
            { name: "Pressure", value: 3.5 },
            { name: "CustomSensor", value: 99 },
          ],
        },
      });

      assert.equal(outputs[0][0].payload.length, 3);
    });
  });

  describe("output modes", () => {
    it("should emit one message per metric in per_metric mode", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: {
          metrics: [
            { name: "Temperature", value: 72 },
            { name: "Pressure", value: 3.5 },
          ],
        },
      });

      // Two send() calls, each is [msg, null]
      assert.equal(outputs.length, 2);
      assert.equal(outputs[0][0].payload.data.measurement_type, "temperature");
      assert.equal(outputs[1][0].payload.data.measurement_type, "pressure");
    });

    it("should emit single message with array in batch mode", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "batch",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: {
          metrics: [
            { name: "Temperature", value: 72 },
            { name: "Pressure", value: 3.5 },
            { name: "Current", value: 12.5 },
          ],
        },
      });

      assert.equal(outputs.length, 1);
      const events = outputs[0][0].payload;
      assert.ok(Array.isArray(events));
      assert.equal(events.length, 3);
      assert.equal(outputs[0][0].iaes_count, 3);
    });
  });

  describe("IAES envelope structure", () => {
    it("should produce valid IAES envelope with all required fields", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
        plant: "Pesqueria",
        area: "Turbinas",
        assetName: "Motor Bomba P-101",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/PlantA/DDATA/GW1/MOTOR-001",
        payload: { metrics: [{ name: "Vibration_Velocity", value: 4.2 }] },
      });

      const iaes = outputs[0][0].payload;

      // Envelope fields
      assert.equal(iaes.spec_version, "1.2");
      assert.equal(iaes.event_type, "asset.measurement");
      assert.ok(iaes.event_id);
      assert.ok(iaes.timestamp);
      assert.ok(iaes.source);

      // Asset fields
      assert.equal(iaes.asset.asset_id, "MOTOR-001");
      assert.equal(iaes.asset.asset_name, "Motor Bomba P-101");
      assert.equal(iaes.asset.plant, "Pesqueria");
      assert.equal(iaes.asset.area, "Turbinas");

      // Data fields
      assert.equal(iaes.data.measurement_type, "vibration_velocity");
      assert.equal(iaes.data.value, 4.2);
      assert.equal(iaes.data.unit, "mm/s");
    });

    it("should auto-derive source from sparkplug topic", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/MyPlant/DDATA/GW-100/Sensor1",
        payload: { metrics: [{ name: "Temp", value: 25 }] },
      });

      assert.equal(outputs[0][0].payload.source, "sparkplug_b.MyPlant.GW-100");
    });

    it("should preserve original metric name as sensor_id", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: { metrics: [{ name: "Bearing/DE/Vibration_Velocity", value: 4.2 }] },
      });

      const iaes = outputs[0][0].payload;
      assert.equal(iaes.data.sensor_id, "Bearing/DE/Vibration_Velocity");
      assert.equal(iaes.data.measurement_type, "vibration_velocity");
    });
  });

  describe("edge cases", () => {
    it("should skip boolean metrics", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "batch",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: {
          metrics: [
            { name: "Temperature", value: 72 },
            { name: "AlarmActive", value: true },
            { name: "Running", value: false },
          ],
        },
      });

      const events = outputs[0][0].payload;
      assert.equal(events.length, 1);
      assert.equal(events[0].data.measurement_type, "temperature");
    });

    it("should handle empty metrics array — error output", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: { metrics: [] },
      });

      // send([null, msg]) → error on port 1
      assert.equal(outputs[0][0], null);
      assert.equal(outputs[0][1].iaes_error, "no_metrics");
    });

    it("should handle missing topic gracefully", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "custom",
        customAssetId: "FALLBACK-001",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: undefined,
        payload: { metrics: [{ name: "Temperature", value: 50 }] },
      });

      assert.equal(outputs[0][0].payload.asset.asset_id, "FALLBACK-001");
    });

    it("should handle non-Sparkplug topic with custom asset ID", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "custom",
        customAssetId: "MY-ASSET",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "some/random/topic",
        payload: { metrics: [{ name: "Pressure", value: 5.5 }] },
      });

      assert.equal(outputs[0][0].payload.asset.asset_id, "MY-ASSET");
    });

    it("should skip metrics with null/undefined values", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "batch",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: {
          metrics: [
            { name: "Temperature", value: 72 },
            { name: "NullMetric", value: null },
            { name: "NoValue" },
          ],
        },
      });

      const events = outputs[0][0].payload;
      assert.equal(events.length, 1);
    });

    it("should handle JSON string payload", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: JSON.stringify({
          metrics: [{ name: "Temperature", value: 72 }],
        }),
      });

      assert.equal(outputs[0][0].payload.data.measurement_type, "temperature");
      assert.equal(outputs[0][0].payload.data.value, 72);
    });

    it("should use engUnit from metric properties when available", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: {
          metrics: [{
            name: "Temperature",
            value: 72,
            properties: { engUnit: { value: "°F" } },
          }],
        },
      });

      assert.equal(outputs[0][0].payload.data.unit, "°F");
    });

    it("should allow msg.asset_id to override configured asset_id", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/OriginalDevice",
        asset_id: "OVERRIDE-001",
        payload: { metrics: [{ name: "Temperature", value: 50 }] },
      });

      assert.equal(outputs[0][0].payload.asset.asset_id, "OVERRIDE-001");
    });
  });

  describe("Sparkplug typed values", () => {
    it("should handle floatValue field", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: { metrics: [{ name: "Temperature", floatValue: 72.5 }] },
      });

      assert.equal(outputs[0][0].payload.data.value, 72.5);
    });

    it("should handle longValue field", () => {
      const node = createNode(RED, "iaes-sparkplug", {
        assetIdSource: "device_id",
        outputMode: "per_metric",
      });

      const { outputs } = sendInput(node, {
        topic: "spBv1.0/G/DDATA/E/D",
        payload: { metrics: [{ name: "Speed", longValue: 1800 }] },
      });

      assert.equal(outputs[0][0].payload.data.value, 1800);
    });
  });
});
