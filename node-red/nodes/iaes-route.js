module.exports = function (RED) {
  var EVENT_TYPES = [
    "asset.measurement",
    "asset.health",
    "maintenance.work_order_intent",
    "maintenance.completion",
    "asset.hierarchy",
    "sensor.registration",
    "maintenance.spare_part_usage",
    // IAES 2.1. Appended, never inserted: the position of a type is the output it
    // leaves by, and a deployed flow is wired to positions. Outputs 1-7 keep their
    // meaning; asset.state gets output 8.
    "asset.state",
  ];
  var OUTPUTS = 8;
  var OTHER = 6;     // output 7: maintenance.spare_part_usage and anything unknown
  var STATE = 7;     // output 8: asset.state

  function empty() {
    var outputs = [];
    for (var i = 0; i < OUTPUTS; i++) outputs.push(null);
    return outputs;
  }

  function IaesRouteNode(config) {
    RED.nodes.createNode(this, config);
    var node = this;

    node.on("input", function (msg, send, done) {
      send = send || function () { node.send.apply(node, arguments); };
      done = done || function (err) { if (err) node.error(err, msg); };

      try {
        var envelope = typeof msg.payload === "string"
          ? JSON.parse(msg.payload)
          : msg.payload;

        if (!envelope || !envelope.event_type) {
          node.status({ fill: "red", shape: "dot", text: "missing event_type" });
          // Route to the "other" output (unknown)
          var outputs = empty();
          msg.payload = envelope;
          msg.iaes_event_type = undefined;
          msg.iaes_asset_id = undefined;
          outputs[OTHER] = msg;
          send(outputs);
          done();
          return;
        }

        var eventType = envelope.event_type;
        var index = EVENT_TYPES.indexOf(eventType);

        msg.payload = envelope;
        msg.iaes_event_type = eventType;
        msg.iaes_asset_id = (envelope.asset && envelope.asset.asset_id) || undefined;

        var outputs = empty();
        if (index >= 0 && index < OTHER) {
          outputs[index] = msg;
        } else if (index === STATE) {
          outputs[STATE] = msg;
        } else {
          // maintenance.spare_part_usage (index 6) or unknown → output 7 (index 6).
          // Output 7 carries both, so flag the unknown case — otherwise a typo
          // in event_type is indistinguishable from a valid spare-part event.
          if (index < 0) msg.iaes_unknown_event_type = true;
          outputs[OTHER] = msg;
        }

        node.status({ fill: "green", shape: "dot", text: eventType });
        send(outputs);
        done();
      } catch (err) {
        node.status({ fill: "red", shape: "dot", text: err.message });
        done(err);
      }
    });
  }

  RED.nodes.registerType("iaes-route", IaesRouteNode);
};
