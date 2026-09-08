const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
// Anchored to the SDK so the suite cannot go stale against the spec again.
const { SPEC_VERSION } = require("@iaes/sdk");

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
        node.status = (s) => { node._status = s; };
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

// send() captures: single-output nodes call send(msg), dual-output call send([msg, null])
// We normalize: outputs[] = array of send() calls. Each call is what was passed to send().
function sendInput(node, msg) {
  const outputs = [];
  const send = function (out) { outputs.push(out); };
  const errors = [];
  const done = function (err) { if (err) errors.push(err); };
  node._handlers.input(msg, send, done);
  return { outputs, errors };
}

// --- Load nodes ---

const RED = createMockRED();
require("../nodes/iaes-measurement.js")(RED);
require("../nodes/iaes-health.js")(RED);
require("../nodes/iaes-work-order.js")(RED);
require("../nodes/iaes-validate.js")(RED);

// --- iaes-measurement (single output: send(msg)) ---

describe("iaes-measurement node", () => {
  it("should create a valid IAES measurement event", () => {
    const node = createNode(RED, "iaes-measurement", {
      assetId: "MOTOR-001",
      measurementType: "vibration_velocity",
      unit: "mm/s",
      source: "test",
    });

    const { outputs, errors } = sendInput(node, { payload: 4.2 });

    assert.equal(errors.length, 0);
    assert.equal(outputs.length, 1);
    const iaes = outputs[0].payload; // send(msg) → msg
    assert.equal(iaes.spec_version, SPEC_VERSION);
    assert.equal(iaes.event_type, "asset.measurement");
    assert.equal(iaes.asset.asset_id, "MOTOR-001");
    assert.equal(iaes.data.measurement_type, "vibration_velocity");
    assert.equal(iaes.data.value, 4.2);
    assert.equal(iaes.data.unit, "mm/s");
  });

  it("should accept string numbers in payload", () => {
    const node = createNode(RED, "iaes-measurement", {
      assetId: "M-1",
      measurementType: "temperature",
      unit: "°C",
    });

    const { outputs } = sendInput(node, { payload: "72.5" });
    assert.equal(outputs[0].payload.data.value, 72.5);
  });

  it("should warn on non-numeric payload", () => {
    const node = createNode(RED, "iaes-measurement", {
      assetId: "M-1",
      measurementType: "temperature",
      unit: "°C",
    });

    sendInput(node, { payload: "not a number" });
    assert.ok(node._warnings.length > 0);
  });

  it("should override config from msg properties", () => {
    const node = createNode(RED, "iaes-measurement", {
      assetId: "DEFAULT",
      measurementType: "temperature",
      unit: "°C",
    });

    const { outputs } = sendInput(node, {
      payload: 5.0,
      asset_id: "OVERRIDE-001",
      measurement_type: "pressure",
      unit: "bar",
    });

    const iaes = outputs[0].payload;
    assert.equal(iaes.asset.asset_id, "OVERRIDE-001");
    assert.equal(iaes.data.measurement_type, "pressure");
    assert.equal(iaes.data.unit, "bar");
  });
});

// --- iaes-health (single output: send(msg)) ---

describe("iaes-health node", () => {
  it("should create a valid IAES health event", () => {
    const node = createNode(RED, "iaes-health", {
      assetId: "MOTOR-001",
      source: "test",
      severity: "critical",
    });

    const { outputs, errors } = sendInput(node, { payload: 0.16 });

    assert.equal(errors.length, 0);
    const iaes = outputs[0].payload;
    assert.equal(iaes.event_type, "asset.health");
    assert.equal(iaes.asset.asset_id, "MOTOR-001");
    assert.equal(iaes.data.health_index, 0.16);
  });
});

// --- iaes-work-order (single output: send(msg)) ---
// Work order reads title from: fields.title (payload obj) || msg.title || config.title

describe("iaes-work-order node", () => {
  it("should create a work order from object payload", () => {
    const node = createNode(RED, "iaes-work-order", {
      assetId: "MOTOR-001",
      source: "test",
      priority: "high",
      triggeredBy: "ai_diagnosis",
    });

    const { outputs, errors } = sendInput(node, {
      payload: {
        title: "Replace bearing DE — critical vibration",
      },
    });

    assert.equal(errors.length, 0);
    const iaes = outputs[0].payload;
    assert.equal(iaes.event_type, "maintenance.work_order_intent");
    assert.equal(iaes.asset.asset_id, "MOTOR-001");
    assert.equal(iaes.data.title, "Replace bearing DE — critical vibration");
    assert.equal(iaes.data.priority, "high");
  });

  it("should read title from msg.title", () => {
    const node = createNode(RED, "iaes-work-order", {
      assetId: "PUMP-001",
      source: "test",
    });

    const { outputs } = sendInput(node, {
      payload: "ignored string",
      title: "Scheduled PM overdue",
    });

    const iaes = outputs[0].payload;
    assert.equal(iaes.data.title, "Scheduled PM overdue");
  });

  it("should read title from config", () => {
    const node = createNode(RED, "iaes-work-order", {
      assetId: "PUMP-001",
      title: "Config title",
      source: "test",
    });

    const { outputs } = sendInput(node, { payload: {} });
    assert.equal(outputs[0].payload.data.title, "Config title");
  });
});

// --- iaes-validate (dual output: send([valid, invalid])) ---

describe("iaes-validate node", () => {
  it("should pass valid IAES events to output 1", () => {
    const node = createNode(RED, "iaes-validate", {});

    // Create a valid event
    const measNode = createNode(RED, "iaes-measurement", {
      assetId: "M-1",
      measurementType: "temperature",
      unit: "°C",
      source: "test",
    });
    const { outputs: measOut } = sendInput(measNode, { payload: 50 });
    const validEnvelope = measOut[0].payload;

    // Validate it
    const { outputs } = sendInput(node, { payload: validEnvelope });
    // send([msg, null]) → outputs[0] = [msg, null]
    assert.ok(outputs[0][0]); // valid output has msg
    assert.equal(outputs[0][0].iaes_event_type, "asset.measurement");
    assert.equal(outputs[0][0].iaes_asset_id, "M-1");
    assert.equal(outputs[0][1], null); // invalid output is null
  });

  it("should reject events missing event_type", () => {
    const node = createNode(RED, "iaes-validate", {});

    const { outputs } = sendInput(node, {
      payload: { asset: { asset_id: "M-1" }, data: {} },
    });

    assert.equal(outputs[0][0], null); // valid is null
    assert.ok(
      outputs[0][1].iaes_errors.includes("Missing required field: event_type")
    );
  });

  it("should reject events missing asset.asset_id", () => {
    const node = createNode(RED, "iaes-validate", {});

    const { outputs } = sendInput(node, {
      payload: { event_type: "asset.measurement", data: {} },
    });

    assert.equal(outputs[0][0], null);
    assert.ok(
      outputs[0][1].iaes_errors.includes("Missing required field: asset")
    );
  });

  // The old node checked event_type, asset.asset_id and data — nothing else —
  // while its documentation promised validation against the JSON schema. These
  // envelopes all passed as valid.
  it("should reject an envelope missing the required envelope fields", () => {
    const node = createNode(RED, "iaes-validate", {});

    const { outputs } = sendInput(node, {
      payload: {
        event_type: "asset.measurement",
        asset: { asset_id: "M-1" },
        data: { measurement_type: "temperature", value: 50, unit: "C" },
      },
    });

    assert.equal(outputs[0][0], null);
    const errors = outputs[0][1].iaes_errors;
    for (const field of ["spec_version", "event_id", "correlation_id", "timestamp", "source"]) {
      assert.ok(
        errors.includes("Missing required field: " + field),
        "expected a complaint about " + field
      );
    }
  });

  it("should reject a malformed source, timestamp and content_hash", () => {
    const node = createNode(RED, "iaes-validate", {});

    const { outputs } = sendInput(node, {
      payload: {
        spec_version: "2.0",
        event_type: "asset.measurement",
        event_id: "11111111-2222-3333-4444-555555555555",
        correlation_id: "11111111-2222-3333-4444-555555555555",
        timestamp: "last tuesday",
        source: "Node RED",
        content_hash: "tooshort",
        asset: { asset_id: "M-1" },
        data: { measurement_type: "temperature", value: 50, unit: "C" },
      },
    });

    assert.equal(outputs[0][0], null);
    const errors = outputs[0][1].iaes_errors.join(" | ");
    assert.ok(errors.includes("timestamp"), "timestamp not flagged");
    assert.ok(errors.includes("source"), "source not flagged");
    assert.ok(errors.includes("content_hash"), "content_hash not flagged");
  });

  it("should reject a measurement missing its required data fields", () => {
    const node = createNode(RED, "iaes-validate", {});

    const measNode = createNode(RED, "iaes-measurement", {
      assetId: "M-1", measurementType: "temperature", unit: "C", source: "test",
    });
    const { outputs: measOut } = sendInput(measNode, { payload: 50 });
    const envelope = measOut[0].payload;
    delete envelope.data.unit;

    const { outputs } = sendInput(node, { payload: envelope });

    assert.equal(outputs[0][0], null);
    assert.ok(outputs[0][1].iaes_errors.includes("Missing required data field: unit"));
  });

  it("should accept JSON string payloads", () => {
    const node = createNode(RED, "iaes-validate", {});

    const measNode = createNode(RED, "iaes-measurement", {
      assetId: "M-1",
      measurementType: "temperature",
      unit: "°C",
      source: "test",
    });
    const { outputs: measOut } = sendInput(measNode, { payload: 50 });
    const envelope = JSON.stringify(measOut[0].payload);

    const { outputs } = sendInput(node, { payload: envelope });
    assert.equal(outputs[0][0].iaes_event_type, "asset.measurement");
  });
});

// --- an open catalog must stay open ---

describe("iaes-validate keeps the catalog open", () => {
  // IAES_SPEC.md: a producer MAY emit its own event_type in a namespace it
  // controls, and a consumer "MUST NOT error" on one it does not recognise.
  // Both flow validators closed the catalog the standard opens — the exact
  // defect 1.4 corrected in the schema, reintroduced in the implementations.
  //
  // Node-RED had two of them: the REQUIRED_DATA_FIELDS lookup, and then
  // fromJSON() called as "the last word", whose typed dispatcher does not know
  // custom types and turned a wire-valid event back into an error.
  const custom = {
    spec_version: SPEC_VERSION,
    event_type: "acme.press_stroke",
    event_id: "550e8400-e29b-41d4-a716-446655440000",
    correlation_id: "550e8400-e29b-41d4-a716-446655440000",
    timestamp: "2026-09-08T12:00:00Z",
    source: "acme.press",
    asset: { asset_id: "PRESS-01" },
    data: { stroke: 42 },
  };

  it("accepts a custom event_type with no dataschema", () => {
    const node = createNode(RED, "iaes-validate", {});
    const { outputs } = sendInput(node, { payload: custom });

    const [valid, invalid] = outputs[0];
    assert.equal(
      invalid, null,
      "a custom event_type was rejected: " +
        JSON.stringify(invalid && invalid.iaes_errors),
    );
    assert.ok(valid, "the event should leave by the valid output");
  });

  it("still rejects an event_type that is not dot-notation", () => {
    // The door opens for a namespaced type, not for anything at all.
    const node = createNode(RED, "iaes-validate", {});
    const { outputs } = sendInput(node, {
      payload: { ...custom, event_type: "NotDotNotation" },
    });
    const [valid, invalid] = outputs[0];
    assert.equal(valid, null, "a malformed event_type must not pass");
    assert.ok(invalid, "it should leave by the invalid output");
  });
});
