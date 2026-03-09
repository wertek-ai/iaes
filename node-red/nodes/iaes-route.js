module.exports = function (RED) {
  var EVENT_TYPES = [
    "asset.measurement",
    "asset.health",
    "maintenance.work_order_intent",
    "maintenance.completion",
    "asset.hierarchy",
    "sensor.registration",
    "maintenance.spare_part_usage",
  ];

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
          // Route to last output (other/unknown)
          var outputs = [null, null, null, null, null, null, null];
          msg.payload = envelope;
          msg.iaes_event_type = undefined;
          msg.iaes_asset_id = undefined;
          outputs[6] = msg;
          send(outputs);
          done();
          return;
        }

        var eventType = envelope.event_type;
        var index = EVENT_TYPES.indexOf(eventType);

        msg.payload = envelope;
        msg.iaes_event_type = eventType;
        msg.iaes_asset_id = (envelope.asset && envelope.asset.asset_id) || undefined;

        var outputs = [null, null, null, null, null, null, null];
        if (index >= 0 && index < 6) {
          outputs[index] = msg;
        } else {
          // maintenance.spare_part_usage (index 6) or unknown → output 7 (index 6)
          outputs[6] = msg;
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
