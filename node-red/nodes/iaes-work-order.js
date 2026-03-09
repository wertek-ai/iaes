module.exports = function (RED) {
  const { WorkOrderIntent } = require("@iaes/sdk");

  function IaesWorkOrderNode(config) {
    RED.nodes.createNode(this, config);
    const node = this;

    node.on("input", function (msg, send, done) {
      send = send || function () { node.send.apply(node, arguments); };
      done = done || function (err) { if (err) node.error(err, msg); };

      try {
        let fields = {};
        if (typeof msg.payload === "object" && msg.payload !== null) {
          fields = msg.payload;
        }

        const event = new WorkOrderIntent({
          asset_id: msg.asset_id || fields.asset_id || config.assetId,
          title: fields.title || msg.title || config.title,
          priority: fields.priority || msg.priority || config.priority || "medium",
          source: msg.source || config.source || "node_red",
          description: fields.description || msg.description || config.description || undefined,
          recommended_due_days: fields.recommended_due_days != null
            ? fields.recommended_due_days
            : (config.recommendedDueDays ? parseInt(config.recommendedDueDays) : undefined),
          triggered_by: fields.triggered_by || msg.triggered_by || config.triggeredBy || undefined,
          asset_name: msg.asset_name || config.assetName || undefined,
          plant: msg.plant || config.plant || undefined,
          area: msg.area || config.area || undefined,
          source_event_id: msg.source_event_id || undefined,
        });

        msg.payload = event.toJSON();
        msg.iaes_event_type = "maintenance.work_order_intent";
        send(msg);
        done();
      } catch (err) {
        done(err);
      }
    });
  }

  RED.nodes.registerType("iaes-work-order", IaesWorkOrderNode);
};
