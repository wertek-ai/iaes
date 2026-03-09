module.exports = function (RED) {
  const { AssetMeasurement } = require("@iaes/sdk");

  function IaesMeasurementNode(config) {
    RED.nodes.createNode(this, config);
    const node = this;

    node.on("input", function (msg, send, done) {
      send = send || function () { node.send.apply(node, arguments); };
      done = done || function (err) { if (err) node.error(err, msg); };

      try {
        const value = typeof msg.payload === "number"
          ? msg.payload
          : parseFloat(msg.payload);

        if (isNaN(value)) {
          node.warn("msg.payload is not a number, skipping");
          done();
          return;
        }

        const event = new AssetMeasurement({
          asset_id: msg.asset_id || config.assetId,
          measurement_type: msg.measurement_type || config.measurementType,
          value: value,
          unit: msg.unit || config.unit,
          source: msg.source || config.source || "node_red",
          sensor_id: msg.sensor_id || config.sensorId || undefined,
          location: msg.location || config.location || undefined,
          units_qualifier: msg.units_qualifier || config.unitsQualifier || undefined,
          asset_name: msg.asset_name || config.assetName || undefined,
          plant: msg.plant || config.plant || undefined,
          area: msg.area || config.area || undefined,
        });

        msg.payload = event.toJSON();
        msg.iaes_event_type = "asset.measurement";
        send(msg);
        done();
      } catch (err) {
        done(err);
      }
    });
  }

  RED.nodes.registerType("iaes-measurement", IaesMeasurementNode);
};
