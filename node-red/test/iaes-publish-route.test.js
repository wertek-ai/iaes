const { describe, it } = require("node:test");
const assert = require("node:assert/strict");

// --- Mock RED (same pattern as iaes-nodes.test.js) ---

function createMockRED() {
  const types = {};
  return {
    nodes: {
      createNode(node, config) {
        node.config = config;
        node._handlers = {};
        node._status = null;
        node.on = (event, fn) => { node._handlers[event] = fn; };
        node.warn = (msg) => { node._warnings = node._warnings || []; node._warnings.push(msg); };
        node.error = (err, msg) => { node._errors = node._errors || []; node._errors.push({ err, msg }); };
        node.send = (msg) => { node._sent = node._sent || []; node._sent.push(msg); };
        node.status = (s) => { node._status = s; };
        node.credentials = config._credentials || {};
      },
      registerType(name, constructor, opts) {
        types[name] = { constructor, opts };
      },
    },
    util: {
      cloneMessage(msg) { return JSON.parse(JSON.stringify(msg)); },
    },
    types,
  };
}

function createNode(RED, typeName, config) {
  const entry = RED.types[typeName];
  const node = {};
  entry.constructor.call(node, config);
  return node;
}

function sendInput(node, msg) {
  const outputs = [];
  const send = function (out) { outputs.push(out); };
  const errors = [];
  const done = function (err) { if (err) errors.push(err); };
  node._handlers.input(msg, send, done);
  return { outputs, errors };
}

// --- Sample IAES envelopes ---

function makeEnvelope(eventType, assetId) {
  return {
    spec_version: "1.2",
    event_type: eventType,
    event_id: "test-" + Date.now(),
    timestamp: new Date().toISOString(),
    source: "test",
    asset: { asset_id: assetId || "MOTOR-001" },
    data: { measurement_type: "vibration_velocity", value: 4.2, unit: "mm/s" },
  };
}

// --- Load nodes ---

const RED = createMockRED();
require("../nodes/iaes-publish.js")(RED);
require("../nodes/iaes-route.js")(RED);

// =============================================
// iaes-publish tests
// =============================================

describe("iaes-publish node", () => {
  it("should register with credentials", () => {
    assert.ok(RED.types["iaes-publish"]);
    assert.ok(RED.types["iaes-publish"].opts);
    assert.ok(RED.types["iaes-publish"].opts.credentials);
    assert.equal(RED.types["iaes-publish"].opts.credentials.apiKey.type, "password");
  });

  it("should create node with config", () => {
    const node = createNode(RED, "iaes-publish", {
      url: "https://example.com",
      batchSize: 1,
      batchTimeout: 5,
    });
    assert.ok(node);
    assert.ok(node._handlers.input);
  });

  it("should error on missing URL", () => {
    const node = createNode(RED, "iaes-publish", {
      url: "",
      batchSize: 1,
      batchTimeout: 5,
    });

    const envelope = makeEnvelope("asset.measurement");
    const { outputs } = sendInput(node, { payload: envelope });

    // Should send to error output (output 2)
    assert.equal(outputs.length, 1);
    assert.equal(outputs[0][0], null); // success is null
    assert.ok(outputs[0][1].payload.error); // error output has message
  });

  it("should error on invalid payload (not IAES)", () => {
    const node = createNode(RED, "iaes-publish", {
      url: "https://example.com",
      batchSize: 1,
      batchTimeout: 5,
    });

    const { outputs } = sendInput(node, { payload: { foo: "bar" } });

    assert.equal(outputs.length, 1);
    assert.equal(outputs[0][0], null);
    assert.ok(outputs[0][1].payload.error.includes("not a valid IAES"));
  });

  it("should parse string payload", () => {
    const node = createNode(RED, "iaes-publish", {
      url: "",
      batchSize: 1,
      batchTimeout: 5,
    });

    const envelope = makeEnvelope("asset.measurement");
    // Will fail on empty URL, but proves JSON.parse worked (no parse error)
    const { outputs } = sendInput(node, { payload: JSON.stringify(envelope) });
    assert.equal(outputs[0][0], null);
    assert.ok(outputs[0][1].payload.error.includes("No URL"));
  });

  it("should error on unparseable string payload", () => {
    const node = createNode(RED, "iaes-publish", {
      url: "https://example.com",
      batchSize: 1,
      batchTimeout: 5,
    });

    const { outputs } = sendInput(node, { payload: "not json{{{" });
    assert.equal(outputs[0][0], null);
    assert.ok(outputs[0][1].payload.error);
  });

  it("should buffer events when batchSize > 1", () => {
    const node = createNode(RED, "iaes-publish", {
      url: "",
      batchSize: 3,
      batchTimeout: 60,
    });

    const e1 = makeEnvelope("asset.measurement", "M-1");
    const e2 = makeEnvelope("asset.health", "M-2");

    // Send 2 events — batch not full yet, should not flush
    const r1 = sendInput(node, { payload: e1 });
    const r2 = sendInput(node, { payload: e2 });

    // No outputs yet (batch size 3 not reached, timeout hasn't fired)
    assert.equal(r1.outputs.length, 0);
    assert.equal(r2.outputs.length, 0);
  });

  it("should flush when batchSize reached", () => {
    const node = createNode(RED, "iaes-publish", {
      url: "",
      batchSize: 2,
      batchTimeout: 60,
    });

    const e1 = makeEnvelope("asset.measurement", "M-1");
    const e2 = makeEnvelope("asset.health", "M-2");

    // First event: buffered
    const r1 = sendInput(node, { payload: e1 });
    assert.equal(r1.outputs.length, 0);

    // Second event: flush triggered (url empty → error output)
    const r2 = sendInput(node, { payload: e2 });
    // The flush sends to both send functions; r2's send will capture the output
    assert.equal(r2.outputs.length, 1);
    assert.ok(r2.outputs[0][1].payload.error.includes("No URL"));
  });

  it("should clean up on close", () => {
    const node = createNode(RED, "iaes-publish", {
      url: "https://example.com",
      batchSize: 10,
      batchTimeout: 5,
    });

    // Send an event to start the timer
    sendInput(node, { payload: makeEnvelope("asset.measurement") });

    // Close should not throw
    assert.ok(node._handlers.close);
    node._handlers.close();
  });
});

// =============================================
// iaes-route tests
// =============================================

describe("iaes-route node", () => {
  it("should route asset.measurement to output 1", () => {
    const node = createNode(RED, "iaes-route", {});
    const envelope = makeEnvelope("asset.measurement", "M-001");
    const { outputs, errors } = sendInput(node, { payload: envelope });

    assert.equal(errors.length, 0);
    assert.equal(outputs.length, 1);
    const out = outputs[0]; // array of 7
    assert.equal(out.length, 7);
    assert.ok(out[0]); // output 1 has the message
    assert.equal(out[0].iaes_event_type, "asset.measurement");
    assert.equal(out[0].iaes_asset_id, "M-001");
    for (let i = 1; i < 7; i++) assert.equal(out[i], null);
  });

  it("should route asset.health to output 2", () => {
    const node = createNode(RED, "iaes-route", {});
    const envelope = makeEnvelope("asset.health", "M-002");
    const { outputs } = sendInput(node, { payload: envelope });
    const out = outputs[0];
    assert.ok(out[1]);
    assert.equal(out[1].iaes_event_type, "asset.health");
    for (let i of [0, 2, 3, 4, 5, 6]) assert.equal(out[i], null);
  });

  it("should route maintenance.work_order_intent to output 3", () => {
    const node = createNode(RED, "iaes-route", {});
    const envelope = makeEnvelope("maintenance.work_order_intent", "P-001");
    const { outputs } = sendInput(node, { payload: envelope });
    const out = outputs[0];
    assert.ok(out[2]);
    assert.equal(out[2].iaes_event_type, "maintenance.work_order_intent");
    for (let i of [0, 1, 3, 4, 5, 6]) assert.equal(out[i], null);
  });

  it("should route maintenance.completion to output 4", () => {
    const node = createNode(RED, "iaes-route", {});
    const envelope = makeEnvelope("maintenance.completion", "P-002");
    const { outputs } = sendInput(node, { payload: envelope });
    const out = outputs[0];
    assert.ok(out[3]);
    assert.equal(out[3].iaes_event_type, "maintenance.completion");
    for (let i of [0, 1, 2, 4, 5, 6]) assert.equal(out[i], null);
  });

  it("should route asset.hierarchy to output 5", () => {
    const node = createNode(RED, "iaes-route", {});
    const envelope = makeEnvelope("asset.hierarchy", "PLANT-001");
    const { outputs } = sendInput(node, { payload: envelope });
    const out = outputs[0];
    assert.ok(out[4]);
    assert.equal(out[4].iaes_event_type, "asset.hierarchy");
    for (let i of [0, 1, 2, 3, 5, 6]) assert.equal(out[i], null);
  });

  it("should route sensor.registration to output 6", () => {
    const node = createNode(RED, "iaes-route", {});
    const envelope = makeEnvelope("sensor.registration", "SENS-001");
    const { outputs } = sendInput(node, { payload: envelope });
    const out = outputs[0];
    assert.ok(out[5]);
    assert.equal(out[5].iaes_event_type, "sensor.registration");
    for (let i of [0, 1, 2, 3, 4, 6]) assert.equal(out[i], null);
  });

  it("should route maintenance.spare_part_usage to output 7 (other)", () => {
    const node = createNode(RED, "iaes-route", {});
    const envelope = makeEnvelope("maintenance.spare_part_usage", "M-003");
    const { outputs } = sendInput(node, { payload: envelope });
    const out = outputs[0];
    assert.ok(out[6]);
    assert.equal(out[6].iaes_event_type, "maintenance.spare_part_usage");
    for (let i = 0; i < 6; i++) assert.equal(out[i], null);
  });

  it("should route unknown event_type to output 7 (other)", () => {
    const node = createNode(RED, "iaes-route", {});
    const envelope = makeEnvelope("custom.future_type", "X-001");
    const { outputs } = sendInput(node, { payload: envelope });
    const out = outputs[0];
    assert.ok(out[6]);
    assert.equal(out[6].iaes_event_type, "custom.future_type");
    assert.equal(out[6].iaes_asset_id, "X-001");
    for (let i = 0; i < 6; i++) assert.equal(out[i], null);
  });

  it("should handle string payload (JSON.parse)", () => {
    const node = createNode(RED, "iaes-route", {});
    const envelope = makeEnvelope("asset.measurement", "M-010");
    const { outputs, errors } = sendInput(node, { payload: JSON.stringify(envelope) });

    assert.equal(errors.length, 0);
    const out = outputs[0];
    assert.ok(out[0]);
    assert.equal(out[0].iaes_event_type, "asset.measurement");
    assert.equal(out[0].iaes_asset_id, "M-010");
  });

  it("should set iaes_event_type and iaes_asset_id on output", () => {
    const node = createNode(RED, "iaes-route", {});
    const envelope = makeEnvelope("asset.health", "PUMP-042");
    const { outputs } = sendInput(node, { payload: envelope });
    const msg = outputs[0][1];
    assert.equal(msg.iaes_event_type, "asset.health");
    assert.equal(msg.iaes_asset_id, "PUMP-042");
  });

  it("should route to output 7 when event_type is missing", () => {
    const node = createNode(RED, "iaes-route", {});
    const { outputs } = sendInput(node, { payload: { asset: { asset_id: "X" }, data: {} } });
    const out = outputs[0];
    assert.ok(out[6]);
    assert.equal(out[6].iaes_event_type, undefined);
    for (let i = 0; i < 6; i++) assert.equal(out[i], null);
  });

  it("should handle invalid JSON string gracefully", () => {
    const node = createNode(RED, "iaes-route", {});
    const { errors } = sendInput(node, { payload: "not valid json{" });
    assert.equal(errors.length, 1);
  });
});
