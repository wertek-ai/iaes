module.exports = function (RED) {
  const { fromJSON } = require("@iaes/sdk");

  // Mirrors schema/iaes-envelope.schema.json + the per-type data schemas.
  // Kept as a table here because the JSON schemas live outside this npm
  // package; the golden test asserts the two stay in step.
  const REQUIRED_ENVELOPE_FIELDS = [
    "spec_version",
    "event_type",
    "event_id",
    "correlation_id",
    "timestamp",
    "source",
    "asset",
    "data",
  ];

  const REQUIRED_DATA_FIELDS = {
    "asset.measurement": ["measurement_type", "value", "unit"],
    "asset.health": ["health_index", "severity"],
    "asset.hierarchy": ["hierarchy_level", "relationship_type"],
    "sensor.registration": ["sensor_id", "registration_status"],
    "maintenance.work_order_intent": ["title", "priority"],
    "maintenance.completion": ["status", "work_order_id"],
    "maintenance.spare_part_usage": [
      "work_order_id",
      "spare_part_id",
      "quantity_used",
    ],
  };

  const SPEC_VERSION_RE = /^1\.[0-9]+$/;
  const SOURCE_RE = /^[a-z][a-z0-9_.]+$/;
  const UUID_RE =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

  /** Collect every problem, not just the first — one pass tells the whole story. */
  function validateEnvelope(envelope) {
    const errors = [];

    if (!envelope || typeof envelope !== "object" || Array.isArray(envelope)) {
      return ["Payload is not a JSON object"];
    }

    for (const field of REQUIRED_ENVELOPE_FIELDS) {
      if (envelope[field] === undefined || envelope[field] === null) {
        errors.push("Missing required field: " + field);
      }
    }

    if (envelope.spec_version != null && !SPEC_VERSION_RE.test(envelope.spec_version)) {
      errors.push(
        'spec_version "' + envelope.spec_version + '" does not match 1.x'
      );
    }

    if (envelope.event_type != null && !REQUIRED_DATA_FIELDS[envelope.event_type]) {
      errors.push('Unknown event_type: "' + envelope.event_type + '"');
    }

    for (const idField of ["event_id", "correlation_id"]) {
      if (envelope[idField] != null && !UUID_RE.test(envelope[idField])) {
        errors.push(idField + " is not a UUID");
      }
    }
    if (envelope.source_event_id != null && !UUID_RE.test(envelope.source_event_id)) {
      errors.push("source_event_id is not a UUID");
    }

    if (envelope.timestamp != null && isNaN(Date.parse(envelope.timestamp))) {
      errors.push("timestamp is not a valid ISO 8601 date-time");
    }

    if (envelope.source != null && !SOURCE_RE.test(envelope.source)) {
      errors.push(
        'source "' + envelope.source +
        '" must be lowercase dot-notation (e.g. acme.diagnostics)'
      );
    }

    // Optional, but when present the length is exact — it is a SHA-256 prefix.
    if (envelope.content_hash != null && String(envelope.content_hash).length !== 16) {
      errors.push("content_hash must be exactly 16 characters");
    }

    if (envelope.asset != null) {
      if (typeof envelope.asset !== "object" || Array.isArray(envelope.asset)) {
        errors.push("asset must be an object");
      } else if (!envelope.asset.asset_id) {
        errors.push("Missing required field: asset.asset_id");
      }
    }

    if (envelope.data != null) {
      if (typeof envelope.data !== "object" || Array.isArray(envelope.data)) {
        errors.push("data must be an object");
      } else {
        const required = REQUIRED_DATA_FIELDS[envelope.event_type] || [];
        for (const field of required) {
          if (envelope.data[field] === undefined || envelope.data[field] === null) {
            errors.push("Missing required data field: " + field);
          }
        }
        if (
          envelope.event_type === "asset.measurement" &&
          envelope.data.value !== undefined &&
          typeof envelope.data.value !== "number"
        ) {
          errors.push("data.value must be a number");
        }
      }
    }

    return errors;
  }

  function IaesValidateNode(config) {
    RED.nodes.createNode(this, config);
    const node = this;

    node.on("input", function (msg, send, done) {
      send = send || function () { node.send.apply(node, arguments); };
      done = done || function (err) { if (err) node.error(err, msg); };

      let envelope;
      try {
        envelope = typeof msg.payload === "string"
          ? JSON.parse(msg.payload)
          : msg.payload;
      } catch (err) {
        msg.iaes_error = "Invalid JSON: " + err.message;
        msg.iaes_errors = [msg.iaes_error];
        node.status({ fill: "red", shape: "dot", text: "invalid JSON" });
        send([null, msg]);
        done();
        return;
      }

      const errors = validateEnvelope(envelope);

      if (errors.length === 0) {
        // Structure is sound; the SDK round-trip is the last word on whether
        // the event actually deserializes.
        try {
          fromJSON(envelope);
        } catch (err) {
          errors.push(err.message);
        }
      }

      if (errors.length > 0) {
        msg.iaes_error = errors[0];
        msg.iaes_errors = errors;
        node.status({
          fill: "red", shape: "dot",
          text: errors.length === 1 ? "1 error" : errors.length + " errors",
        });
        send([null, msg]);
        done();
        return;
      }

      msg.payload = envelope;
      msg.iaes_event_type = envelope.event_type;
      msg.iaes_asset_id = envelope.asset.asset_id;
      node.status({ fill: "green", shape: "dot", text: envelope.event_type });
      send([msg, null]);
      done();
    });
  }

  RED.nodes.registerType("iaes-validate", IaesValidateNode);
};
