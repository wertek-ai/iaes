/**
 * The Node-RED iaes-validate node against the shared conformance cases
 * (conformance/), in both modes, plus a node saved before the Strict option
 * existed. The same cases run in the Python SDK, the TypeScript SDK and the
 * n8n nodes; see conformance/README.md.
 */

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const DIR = path.join(__dirname, "..", "..", "conformance");
const CASES = JSON.parse(fs.readFileSync(path.join(DIR, "validation.json"), "utf-8")).cases;

function createMockRED() {
  const types = {};
  return {
    nodes: {
      createNode(node, config) {
        node.config = config;
        node._handlers = {};
        node.on = (event, fn) => { node._handlers[event] = fn; };
        node.error = (err) => { throw err; };
        node.status = () => {};
      },
      registerType(name, constructor) { types[name] = constructor; },
    },
    types,
  };
}

const RED = createMockRED();
require("../nodes/iaes-validate.js")(RED);

/** One message through a fresh node; returns which output it left by. */
function run(event, config) {
  const node = {};
  RED.types["iaes-validate"].call(node, config);
  let out = null;
  let failure = null;
  node._handlers.input(
    { payload: JSON.parse(JSON.stringify(event)) },
    (o) => { out = o; },
    (err) => { if (err) failure = err; },
  );
  // A validator that fails is not a verdict: surface it.
  if (failure) throw failure;
  const [valid, invalid] = out;
  return { valid: valid !== null, msg: valid || invalid };
}

describe("iaes-validate against conformance/validation.json", () => {
  for (const c of CASES) {
    it(`default mode: ${c.id}`, () => {
      const r = run(c.event, { strict: false });
      assert.equal(r.valid, c.expect.schema_valid, c.title);
      if (c.expect.schema_valid) {
        assert.deepEqual(r.msg.iaes_nonconformities, c.expect.nonconforming_fields, c.title);
      }
    });

    it(`strict mode: ${c.id}`, () => {
      assert.equal(run(c.event, { strict: true }).valid, c.expect.conforming, c.title);
    });
  }
});

describe("a node saved before the Strict option existed", () => {
  it("keeps rejecting what it rejected: an event_id that is not a UUID", () => {
    // Its config has no `strict`. Before this suite it rejected non-UUID
    // identifiers by default, and a package update must not change what a
    // deployed flow accepts.
    const c = CASES.find((x) => x.id === "nonconforming.event_id");
    assert.equal(run(c.event, {}).valid, false);
  });
});
