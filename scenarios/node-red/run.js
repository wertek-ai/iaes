#!/usr/bin/env node
/**
 * The reference scenarios, in Node-RED.
 *
 * The scenario IS `flow.json` -- the file an integrator imports. This script
 * does not re-tell the story in code: it boots a real Node-RED runtime, loads
 * that file unchanged, presses the inject node, and prints what the `IAES
 * events` debug node received. `tests/test_reference_scenarios.py` checks the
 * output against `scenarios/fixture.json` alongside the other implementations.
 *
 * Run it:
 *
 *     node scenarios/node-red/run.js            # prints the events
 *     node scenarios/node-red/run.js out.json   # writes them
 *
 * It needs `node-red/node_modules` (run `npm ci` in node-red/): the runtime
 * and the test helper are dev dependencies there. Reported rather than
 * guessed: if they are missing this script says so and exits non-zero.
 *
 * ### Why a real runtime
 *
 * A mock RED can drive one node. It cannot prove that a `change` node's rules
 * carry the chain forward, that a `function` node's Modules setup resolves
 * `@iaes/sdk`, or that the wires deliver the five events in order -- and those
 * are exactly what the flow claims. Running a flow with a mock would check
 * our nodes and assume the flow. This checks the flow.
 *
 * The only substitution: the two `debug` nodes become the helper's `helper`
 * nodes, which is how node-red-node-test-helper captures output. Same ids,
 * same wires, nothing else touched.
 */

"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { createRequire } = require("node:module");

const ROOT = path.resolve(__dirname, "..", "..");
const PACKAGE_DIR = path.join(ROOT, "node-red");
const FLOW = path.join(__dirname, "flow.json");

// Resolve node-red, the helper and the core nodes from the package's own
// node_modules, wherever this script is run from. The helper finds the
// package under test by walking up from process.cwd() to a package.json that
// depends on node-red, so the working directory has to be the package too.
const packageRequire = createRequire(path.join(PACKAGE_DIR, "package.json"));
process.chdir(PACKAGE_DIR);

function fail(message) {
  process.stderr.write(`reference scenarios (node-red): ${message}\n`);
  process.exit(1);
}

let helper;
let nodeRedPath;
try {
  helper = packageRequire("node-red-node-test-helper");
  nodeRedPath = packageRequire.resolve("node-red");
} catch (err) {
  fail(
    "node-red or node-red-node-test-helper is not installed. Run `npm ci` in " +
      "node-red/ (they are dev dependencies). Reported rather than skipped: a " +
      `skipped check is one that stopped checking. (${err.message})`
  );
}

// The flow, unchanged, except that debug nodes become capture nodes.
const flow = JSON.parse(fs.readFileSync(FLOW, "utf-8")).map((node) =>
  node.type === "debug" ? { ...node, type: "helper" } : node
);

const ours = ["iaes-measurement", "iaes-health", "iaes-work-order", "iaes-validate"].map(
  (name) => require(path.join(PACKAGE_DIR, "nodes", `${name}.js`))
);
// Every core type the flow uses. Node-RED refuses to start a flow with a
// missing type, and then every getNode() is null -- so this list is checked
// against the flow below rather than trusted.
const core = ["common/20-inject.js", "common/90-comment.js", "function/15-change.js", "function/10-function.js"].map(
  (rel) => packageRequire(`@node-red/nodes/core/${rel}`)
);

const EXPECTED = 5;
const TIMEOUT_MS = 20000;

async function run() {
  // `userDir` is the package directory so a function node's Modules setup
  // resolves `@iaes/sdk` from node_modules that already exist. Without it
  // Node-RED would `npm install` the module at load time -- which is what a
  // real Node-RED does for a user, and what hung this script for three
  // minutes when tried in a temporary userDir.
  helper.init(nodeRedPath, { functionExternalModules: true, userDir: PACKAGE_DIR });
  await helper.startServer();
  await helper.load([...ours, ...core], flow);

  const events = [];
  const collector = helper.getNode("events");
  const invalid = helper.getNode("invalid");
  const inject = helper.getNode("reading");
  if (!collector || !invalid || !inject) {
    const missing = ["events", "invalid", "reading"].filter((id) => !helper.getNode(id));
    fail(`nodes ${JSON.stringify(missing)} did not start. Either flow.json lost them or the flow uses a node type this script does not load: ` +
      JSON.stringify([...new Set(flow.map((n) => n.type))]));
  }

  const done = new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error(`received ${events.length} of ${EXPECTED} events in ${TIMEOUT_MS} ms`)),
      TIMEOUT_MS
    );
    collector.on("input", (msg) => {
      events.push(msg.payload);
      if (events.length === EXPECTED) {
        clearTimeout(timer);
        resolve();
      }
    });
    invalid.on("input", (msg) => {
      clearTimeout(timer);
      reject(new Error(`iaes-validate rejected an event: ${JSON.stringify(msg.iaes_errors)}`));
    });
  });

  // Press the inject node. Its configured payload is the reading.
  inject.receive({});
  await done;

  await helper.unload();
  await helper.stopServer();
  return events;
}

run()
  .then((events) => {
    const text = JSON.stringify(events, null, 2);
    if (process.argv[2]) fs.writeFileSync(process.argv[2], text, "utf-8");
    else process.stdout.write(text + "\n");
    process.exit(0);
  })
  .catch((err) => fail(err.stack || err.message));
