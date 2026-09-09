#!/usr/bin/env node
/**
 * The reference scenarios, in n8n.
 *
 * The scenario IS `workflow.json` -- the file an integrator imports. This
 * script walks that file's connections from the trigger, executes each node,
 * and prints the five events the workflow emits. `tests/test_reference_scenarios.py`
 * checks them against `scenarios/fixture.json` alongside the other
 * implementations.
 *
 * Run it:
 *
 *     node scenarios/n8n/run.js            # prints the events
 *     node scenarios/n8n/run.js out.json   # writes them
 *
 * It needs `n8n-nodes/dist` (run `npm ci && npm run build` in n8n-nodes/):
 * the nodes are executed from the COMPILED package, which is what n8n loads.
 *
 * ### What runs for real and what is stood in for -- said out loud
 *
 * There is no n8n runtime that can be booted the way node-red-node-test-helper
 * boots Node-RED: executing a workflow needs the whole n8n editor/runner
 * stack. So this script is honest about its two halves:
 *
 *   REAL      the package's own nodes (`iaesEmit`, `iaesValidate`), executed
 *             from `dist/` with the context n8n gives them: `getInputData()`
 *             and `getNodeParameter()` over the workflow's parameters.
 *
 *   STOOD IN  three n8n core nodes the workflow uses, replaced by the smallest
 *             stand-in that does what their documentation says, and nothing
 *             else: `manualTrigger` (one empty item), `crypto` in `generate`
 *             mode with `uuid` (adds a UUID to the named property), and `set`
 *             in `raw` mode (a JSON template with expressions, other fields
 *             dropped). Expressions are limited to `{{ $json.<path> }}` and
 *             `{{ JSON.stringify($json.<path>) }}`; anything else is refused
 *             rather than guessed at. A node type outside this list stops the
 *             script with its name.
 *
 * The parameter values that reach the REAL nodes are exactly the workflow's,
 * expressions resolved from the previous node's item -- so what this proves
 * is that THOSE parameters, given to THOSE nodes, produce the fixture's
 * events. What it cannot prove is that n8n's own core nodes behave as their
 * stand-ins do. That is declared here, not hidden behind a green run.
 */

"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { randomUUID } = require("node:crypto");

const ROOT = path.resolve(__dirname, "..", "..");
const PACKAGE_DIR = path.join(ROOT, "n8n-nodes");
const DIST = path.join(PACKAGE_DIR, "dist", "nodes");
const WORKFLOW = path.join(__dirname, "workflow.json");

function fail(message) {
  process.stderr.write(`reference scenarios (n8n): ${message}\n`);
  process.exit(1);
}

if (!fs.existsSync(path.join(DIST, "IaesEmit", "IaesEmit.node.js"))) {
  fail(
    "n8n-nodes/dist is not built. This script executes the compiled nodes, " +
      "which is what n8n loads; run `npm ci && npm run build` in n8n-nodes/. " +
      "Reported rather than skipped: a skipped check is one that stopped checking."
  );
}

const { IaesEmit } = require(path.join(DIST, "IaesEmit", "IaesEmit.node.js"));
const { IaesValidate } = require(path.join(DIST, "IaesValidate", "IaesValidate.node.js"));

const workflow = JSON.parse(fs.readFileSync(WORKFLOW, "utf-8"));
const byName = new Map(workflow.nodes.map((n) => [n.name, n]));

// ---- expressions: the declared subset -------------------------------------

const WHOLE = /^=\{\{\s*(JSON\.stringify\()?\$json((?:\.[A-Za-z_][A-Za-z0-9_]*)+)\)?\s*\}\}$/;
const INLINE = /\{\{\s*(JSON\.stringify\()?\$json((?:\.[A-Za-z_][A-Za-z0-9_]*)+)\)?\s*\}\}/g;

function lookup(json, dotted, where) {
  let value = json;
  for (const key of dotted.split(".").filter(Boolean)) {
    if (value === null || typeof value !== "object" || !(key in value)) {
      fail(`${where}: $json${dotted} is not present on the incoming item`);
    }
    value = value[key];
  }
  return value;
}

/** A parameter that is a whole expression resolves to the VALUE, as in n8n. */
function resolveParameter(raw, json, where) {
  if (typeof raw !== "string" || !raw.startsWith("=")) return raw;
  const m = WHOLE.exec(raw);
  if (!m) fail(`${where}: expression ${JSON.stringify(raw)} is outside the subset this script supports`);
  const value = lookup(json, m[2], where);
  return m[1] ? JSON.stringify(value) : value;
}

/** A raw-JSON template resolves each expression inline, then parses. */
function resolveTemplate(raw, json, where) {
  if (!raw.startsWith("=")) return JSON.parse(raw);
  const text = raw.slice(1).replace(INLINE, (_, stringify, dotted) => {
    const value = lookup(json, dotted, where);
    return stringify ? JSON.stringify(value) : String(value);
  });
  if (/\{\{/.test(text)) fail(`${where}: template still contains an expression outside the supported subset`);
  return JSON.parse(text);
}

// ---- node execution --------------------------------------------------------

/** The context n8n hands a node: its input items and its parameters. */
function contextFor(node, NodeClass, items) {
  const defaults = new Map(new NodeClass().description.properties.map((p) => [p.name, p.default]));
  return {
    getInputData: () => items,
    getNodeParameter(name, i) {
      const where = `${node.name} / ${name}`;
      if (name in node.parameters) return resolveParameter(node.parameters[name], items[i].json, where);
      if (defaults.has(name)) return defaults.get(name);
      fail(`${where}: not a parameter of ${node.type}`);
    },
  };
}

async function execute(node, items) {
  switch (node.type) {
    case "n8n-nodes-base.manualTrigger":
      return [[{ json: {} }]];
    case "n8n-nodes-iaes.iaesEmit":
      return new IaesEmit().execute.call(contextFor(node, IaesEmit, items));
    case "n8n-nodes-iaes.iaesValidate":
      return new IaesValidate().execute.call(contextFor(node, IaesValidate, items));
    case "n8n-nodes-base.crypto": {
      const p = node.parameters;
      if (p.action !== "generate" || p.encodingType !== "uuid") fail(`${node.name}: only crypto generate/uuid is stood in for`);
      return [items.map((it) => ({ json: { ...it.json, [p.dataPropertyName]: randomUUID() } }))];
    }
    case "n8n-nodes-base.set": {
      const p = node.parameters;
      if (p.mode !== "raw" || p.includeOtherFields) fail(`${node.name}: only set in raw mode without other fields is stood in for`);
      return [items.map((it) => ({ json: resolveTemplate(p.jsonOutput, it.json, node.name) }))];
    }
    default:
      fail(`${node.name}: node type ${node.type} is not executed by this script`);
  }
}

function next(node) {
  const outs = (workflow.connections[node.name] || {}).main || [];
  const targets = outs[0] || []; // output 0: the only path the story follows
  if (targets.length > 1) fail(`${node.name}: the story is linear, found ${targets.length} targets`);
  return targets.length ? byName.get(targets[0].node) : null;
}

async function run() {
  const trigger = workflow.nodes.find((n) => n.type === "n8n-nodes-base.manualTrigger");
  if (!trigger) fail("workflow.json has no manual trigger");

  const events = [];
  let node = trigger;
  let items = [];
  while (node) {
    const outputs = await execute(node, items);
    if (node.type === "n8n-nodes-iaes.iaesValidate") {
      const [valid, invalid] = outputs;
      if (invalid.length) fail(`${node.name} rejected an event: ${JSON.stringify(invalid[0].json.iaes_validation.errors)}`);
      if (valid.length !== 1) fail(`${node.name} passed ${valid.length} items, expected 1`);
    } else if (node.type === "n8n-nodes-iaes.iaesEmit" || node.type === "n8n-nodes-base.set") {
      // What a consumer receives: the envelope as emitted, before the
      // validator annotates it with iaes_validation.
      events.push(outputs[0][0].json);
    }
    items = outputs[0];
    node = next(node);
  }
  return events;
}

run()
  .then((events) => {
    const text = JSON.stringify(events, null, 2);
    if (process.argv[2]) fs.writeFileSync(process.argv[2], text, "utf-8");
    else process.stdout.write(text + "\n");
  })
  .catch((err) => fail(err.stack || err.message));
