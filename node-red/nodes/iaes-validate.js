module.exports = function (RED) {
  const { validate, ValidationError, findNonconformities } = require("@iaes/sdk");

  // This node keeps no rules of its own. It used to: a list of required
  // fields per type, a regex for spec_version, one for event_type, one for
  // source and one for UUIDs -- a fourth copy of the standard, and it drifted.
  // Measured on 2026-10-06 against the shared cases in conformance/: it
  // accepted spec_version "205" (the regex was built from a JS string, where
  // "\." is just "."), and it rejected events with a non-UUID event_id that
  // every other validator accepts.
  //
  // Now there are two verdicts, the same two the specification separates
  // (IAES_SPEC.md, "An event can be schema-valid and non-conforming"):
  //
  //   - schema: the SDK's validate(), against the published schemas;
  //   - conformance: the SDK's findNonconformities(), which checks the fields
  //     the schemas annotate with a format (uuid, date-time, date, uri).
  //
  // The Python SDK, the TypeScript SDK and the n8n nodes give the same two
  // answers for the same event; conformance/ is where that is measured.
  //
  // Strict mode routes a nonconforming event to the invalid output. Off, it is
  // routed as valid and its fields are named in msg.iaes_nonconformities.
  // A node saved before this option existed has no `strict` in its config and
  // keeps rejecting, as it did: a deployed flow must not start accepting events
  // it used to reject because a package was updated.

  function describe(field) {
    return field + " does not conform to the specification";
  }

  function IaesValidateNode(config) {
    RED.nodes.createNode(this, config);
    const node = this;
    const strict = config.strict !== false;

    node.on("input", function (msg, send, done) {
      send = send || function () { node.send.apply(node, arguments); };
      done = done || function (err) { if (err) node.error(err, msg); };

      function reject(errors, text) {
        msg.iaes_error = errors[0];
        msg.iaes_errors = errors;
        node.status({ fill: "red", shape: "dot", text: text });
        send([null, msg]);
        done();
      }

      let envelope;
      try {
        envelope = typeof msg.payload === "string" ? JSON.parse(msg.payload) : msg.payload;
      } catch (err) {
        reject(["Invalid JSON: " + err.message], "invalid JSON");
        return;
      }

      try {
        validate(envelope);
      } catch (err) {
        if (!(err instanceof ValidationError)) {
          // Not a verdict: the validator itself failed (for example, ajv is
          // missing). Reported as an error, never as "invalid event".
          done(err);
          return;
        }
        // Every problem in one pass: in strict mode the nonconforming fields
        // are reported alongside what the schema rejected.
        const nonconforming = findNonconformities(envelope);
        msg.iaes_nonconformities = nonconforming;
        const errors = (err.errors && err.errors.length ? err.errors : [err.message])
          .concat(strict ? nonconforming.map(describe) : []);
        reject(errors, errors.length === 1 ? "1 error" : errors.length + " errors");
        return;
      }

      const nonconforming = findNonconformities(envelope);
      msg.iaes_nonconformities = nonconforming;
      if (nonconforming.length > 0 && strict) {
        reject(
          nonconforming.map(describe),
          nonconforming.length === 1 ? "1 nonconforming field" : nonconforming.length + " nonconforming fields",
        );
        return;
      }

      msg.payload = envelope;
      msg.iaes_event_type = envelope.event_type;
      msg.iaes_asset_id = envelope.asset.asset_id;
      node.status(
        nonconforming.length > 0
          ? { fill: "yellow", shape: "ring", text: envelope.event_type + " (nonconforming)" }
          : { fill: "green", shape: "dot", text: envelope.event_type },
      );
      send([msg, null]);
      done();
    });
  }

  RED.nodes.registerType("iaes-validate", IaesValidateNode);
};
