module.exports = function (RED) {
  const { fromJSON } = require("@iaes/sdk");

  function IaesValidateNode(config) {
    RED.nodes.createNode(this, config);
    const node = this;

    node.on("input", function (msg, send, done) {
      send = send || function () { node.send.apply(node, arguments); };
      done = done || function (err) { if (err) node.error(err, msg); };

      try {
        const envelope = typeof msg.payload === "string"
          ? JSON.parse(msg.payload)
          : msg.payload;

        // Validate by attempting to deserialize with the SDK
        if (!envelope || !envelope.event_type) {
          msg.iaes_error = "Missing event_type field";
          send([null, msg]);
          done();
          return;
        }

        if (!envelope.asset || !envelope.asset.asset_id) {
          msg.iaes_error = "Missing asset.asset_id field";
          send([null, msg]);
          done();
          return;
        }

        if (!envelope.data || typeof envelope.data !== "object") {
          msg.iaes_error = "Missing or invalid data field";
          send([null, msg]);
          done();
          return;
        }

        // Try to deserialize — this validates the event_type is known
        const event = fromJSON(envelope);
        msg.payload = envelope;
        msg.iaes_event_type = envelope.event_type;
        msg.iaes_asset_id = envelope.asset.asset_id;
        send([msg, null]);
        done();
      } catch (err) {
        msg.iaes_error = err.message;
        send([null, msg]);
        done();
      }
    });
  }

  RED.nodes.registerType("iaes-validate", IaesValidateNode);
};
