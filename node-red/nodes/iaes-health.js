module.exports = function (RED) {
  const { AssetHealth } = require("@iaes/sdk");

  function IaesHealthNode(config) {
    RED.nodes.createNode(this, config);
    const node = this;

    node.on("input", function (msg, send, done) {
      send = send || function () { node.send.apply(node, arguments); };
      done = done || function (err) { if (err) node.error(err, msg); };

      try {
        // msg.payload can be a health_index number or an object with fields
        let fields = {};
        if (typeof msg.payload === "number") {
          fields.health_index = msg.payload;
        } else if (typeof msg.payload === "object" && msg.payload !== null) {
          fields = msg.payload;
        }

        const event = new AssetHealth({
          asset_id: msg.asset_id || config.assetId,
          health_index: fields.health_index != null ? fields.health_index : parseFloat(config.healthIndex) || 1.0,
          severity: fields.severity || msg.severity || config.severity || "info",
          source: msg.source || config.source || "node_red",
          failure_mode: fields.failure_mode || msg.failure_mode || config.failureMode || undefined,
          rul_days: fields.rul_days != null ? fields.rul_days : (config.rulDays ? parseInt(config.rulDays) : undefined),
          recommended_action: fields.recommended_action || msg.recommended_action || config.recommendedAction || undefined,
          anomaly_score: fields.anomaly_score != null ? fields.anomaly_score : (config.anomalyScore ? parseFloat(config.anomalyScore) : 0.0),
          fault_confidence: fields.fault_confidence != null ? fields.fault_confidence : (config.faultConfidence ? parseFloat(config.faultConfidence) : 0.0),
          iso_13374_status: fields.iso_13374_status || msg.iso_13374_status || config.iso13374Status || undefined,
          asset_name: msg.asset_name || config.assetName || undefined,
          plant: msg.plant || config.plant || undefined,
          area: msg.area || config.area || undefined,
          source_event_id: msg.source_event_id || undefined,
        });

        msg.payload = event.toJSON();
        msg.iaes_event_type = "asset.health";
        send(msg);
        done();
      } catch (err) {
        done(err);
      }
    });
  }

  RED.nodes.registerType("iaes-health", IaesHealthNode);
};
