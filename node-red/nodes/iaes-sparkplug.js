module.exports = function (RED) {
  const { AssetMeasurement } = require("@iaes/sdk");

  // Sparkplug B topic: spBv1.0/{group_id}/{message_type}/{edge_node_id}/{device_id}
  function parseSparkplugTopic(topic) {
    if (!topic) return null;
    const parts = topic.split("/");
    if (parts.length < 4 || parts[0] !== "spBv1.0") return null;
    return {
      group_id: parts[1],
      message_type: parts[2],
      edge_node_id: parts[3],
      device_id: parts[4] || parts[3], // NDATA has no device_id, use edge_node_id
    };
  }

  // Auto-detect measurement_type from Sparkplug metric name
  // Covers common naming conventions from Ignition, Cirrus Link, Banner DXM, etc.
  const METRIC_TYPE_MAP = {
    // Vibration
    "vibration": "vibration_velocity",
    "vibration_velocity": "vibration_velocity",
    "vibration_acceleration": "vibration_acceleration",
    "vibration_displacement": "vibration_displacement",
    "velocity": "vibration_velocity",
    "acceleration": "vibration_acceleration",
    "vib_vel": "vibration_velocity",
    "vib_acc": "vibration_acceleration",
    // Temperature
    "temperature": "temperature",
    "temp": "temperature",
    // Electrical
    "current": "current",
    "voltage": "voltage",
    "power": "power",
    "energy": "energy",
    "power_factor": "power_factor",
    "pf": "power_factor",
    "thd": "thd_voltage",
    "thd_voltage": "thd_voltage",
    "thd_current": "thd_current",
    "frequency": "frequency",
    "reactive_power": "reactive_power",
    // Process
    "pressure": "pressure",
    "flow": "flow",
    "speed": "speed",
    "rpm": "speed",
    "level": "level",
  };

  function inferMeasurementType(metricName) {
    if (!metricName) return "custom";
    // Normalize: lowercase, replace spaces/dashes/dots with underscore
    const normalized = metricName.toLowerCase().replace(/[\s\-./]+/g, "_");

    // Direct match
    if (METRIC_TYPE_MAP[normalized]) return METRIC_TYPE_MAP[normalized];

    // Partial match — check if any known key is contained in the metric name
    for (const [key, type] of Object.entries(METRIC_TYPE_MAP)) {
      if (normalized.includes(key)) return type;
    }

    return "custom";
  }

  // Common unit inference from Sparkplug metric properties
  const TYPE_DEFAULT_UNITS = {
    "vibration_velocity": "mm/s",
    "vibration_acceleration": "g",
    "vibration_displacement": "um",
    "temperature": "°C",
    "current": "A",
    "voltage": "V",
    "power": "kW",
    "energy": "kWh",
    "power_factor": "ratio",
    "thd_voltage": "%",
    "thd_current": "%",
    "frequency": "Hz",
    "reactive_power": "kVAR",
    "pressure": "bar",
    "flow": "m3/h",
    "speed": "rpm",
    "level": "m",
  };

  function decodeSparkplugPayload(buf) {
    // Try sparkplug-payload library first (protobuf)
    try {
      const sparkplug = require("sparkplug-payload");
      const decoder = sparkplug.get("spBv1.0");
      return decoder.decodePayload(buf);
    } catch (_e) {
      // Fallback: try JSON (some gateways send JSON on Sparkplug topics)
      if (Buffer.isBuffer(buf)) {
        return JSON.parse(buf.toString("utf8"));
      }
      if (typeof buf === "string") {
        return JSON.parse(buf);
      }
      // Already an object
      return buf;
    }
  }

  function IaesSparkplugNode(config) {
    RED.nodes.createNode(this, config);
    const node = this;

    node.on("input", function (msg, send, done) {
      send = send || function () { node.send.apply(node, arguments); };
      done = done || function (err) { if (err) node.error(err, msg); };

      try {
        // Parse Sparkplug topic
        const topicInfo = parseSparkplugTopic(msg.topic);

        // Decode payload (protobuf or JSON)
        let decoded;
        try {
          decoded = decodeSparkplugPayload(msg.payload);
        } catch (err) {
          node.warn("Failed to decode Sparkplug payload: " + err.message);
          msg.iaes_error = "decode_failed: " + err.message;
          send([null, msg]);
          done();
          return;
        }

        // Extract metrics array
        const metrics = decoded.metrics || decoded.Metrics || [];
        if (!Array.isArray(metrics) || metrics.length === 0) {
          node.warn("No metrics found in Sparkplug payload");
          msg.iaes_error = "no_metrics";
          send([null, msg]);
          done();
          return;
        }

        // Determine asset_id
        const assetIdMode = config.assetIdSource || "device_id";
        let baseAssetId;
        if (assetIdMode === "custom" && config.customAssetId) {
          baseAssetId = config.customAssetId;
        } else if (assetIdMode === "edge_node" && topicInfo) {
          baseAssetId = topicInfo.edge_node_id;
        } else if (topicInfo) {
          baseAssetId = topicInfo.device_id;
        } else {
          baseAssetId = config.customAssetId || "unknown";
        }

        // Apply metric filter if configured
        const filterRegex = config.metricFilter
          ? new RegExp(config.metricFilter, "i")
          : null;

        // Build source identifier
        const source = config.source || (topicInfo
          ? "sparkplug_b." + topicInfo.group_id + "." + topicInfo.edge_node_id
          : "sparkplug_b");

        const events = [];
        const skipped = [];

        for (const metric of metrics) {
          const name = metric.name || metric.Name;
          if (!name) continue;

          // Apply filter
          if (filterRegex && !filterRegex.test(name)) {
            skipped.push(name);
            continue;
          }

          // Extract value — Sparkplug uses typed value fields
          let value = metric.value !== undefined ? metric.value
            : metric.floatValue !== undefined ? metric.floatValue
            : metric.doubleValue !== undefined ? metric.doubleValue
            : metric.intValue !== undefined ? metric.intValue
            : metric.longValue !== undefined ? metric.longValue
            : undefined;

          if (value === undefined || value === null) continue;
          value = Number(value);
          if (isNaN(value)) continue;

          // Boolean metrics (e.g. alarms) — skip unless explicitly included
          if (typeof metric.value === "boolean") continue;

          const measType = inferMeasurementType(name);
          const unit = metric.properties && metric.properties.engUnit
            ? metric.properties.engUnit.value || metric.properties.engUnit
            : TYPE_DEFAULT_UNITS[measType] || "";

          const event = new AssetMeasurement({
            asset_id: msg.asset_id || baseAssetId,
            measurement_type: measType,
            value: value,
            unit: unit,
            source: source,
            sensor_id: metric.name || undefined,
            asset_name: config.assetName || undefined,
            plant: config.plant || (topicInfo ? topicInfo.group_id : undefined),
            area: config.area || undefined,
          });

          events.push(event.toJSON());
        }

        if (events.length === 0) {
          msg.iaes_error = "no_numeric_metrics";
          msg.iaes_skipped = skipped;
          send([null, msg]);
          done();
          return;
        }

        // Output mode
        if (config.outputMode === "batch") {
          // Single message with array of IAES events
          msg.payload = events;
          msg.iaes_event_type = "asset.measurement";
          msg.iaes_count = events.length;
          msg.iaes_asset_id = baseAssetId;
          if (skipped.length) msg.iaes_skipped = skipped;
          send([msg, null]);
        } else {
          // One message per metric (default)
          for (let i = 0; i < events.length; i++) {
            const out = i === 0 ? msg : RED.util.cloneMessage(msg);
            out.payload = events[i];
            out.iaes_event_type = "asset.measurement";
            out.iaes_asset_id = events[i].asset.asset_id;
            if (i === 0 && skipped.length) out.iaes_skipped = skipped;
            send([out, null]);
          }
        }

        done();
      } catch (err) {
        done(err);
      }
    });
  }

  RED.nodes.registerType("iaes-sparkplug", IaesSparkplugNode);
};
