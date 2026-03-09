module.exports = function (RED) {
  const https = require("https");
  const http = require("http");
  const url = require("url");

  function IaesPublishNode(config) {
    RED.nodes.createNode(this, config);
    const node = this;
    const batchSize = parseInt(config.batchSize, 10) || 1;
    const batchTimeout = (parseFloat(config.batchTimeout) || 5) * 1000;
    const buffer = [];
    let timer = null;

    function flush() {
      if (timer) { clearTimeout(timer); timer = null; }
      if (buffer.length === 0) return;

      const batch = buffer.splice(0, buffer.length);
      const lastMsg = batch[batch.length - 1].msg;
      const events = batch.map(function (item) { return item.envelope; });
      const sends = batch.map(function (item) { return item.send; });
      const dones = batch.map(function (item) { return item.done; });

      const targetUrl = config.url;
      if (!targetUrl) {
        var errMsg = "No URL configured";
        node.status({ fill: "red", shape: "dot", text: errMsg });
        sends.forEach(function (s) {
          s([null, { payload: { error: errMsg } }]);
        });
        dones.forEach(function (d) { d(); });
        return;
      }

      var endpoint = targetUrl.replace(/\/+$/, "") + "/api/v1/iaes/ingest";
      var parsed = url.parse(endpoint);
      var transport = parsed.protocol === "https:" ? https : http;
      var apiKey = (node.credentials && node.credentials.apiKey) || "";

      var body = JSON.stringify(events.length === 1 ? events[0] : events);

      var options = {
        hostname: parsed.hostname,
        port: parsed.port || (parsed.protocol === "https:" ? 443 : 80),
        path: parsed.path,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body),
        },
      };

      if (apiKey) {
        options.headers["Authorization"] = "Bearer " + apiKey;
      }

      var req = transport.request(options, function (res) {
        var data = "";
        res.on("data", function (chunk) { data += chunk; });
        res.on("end", function () {
          var statusCode = res.statusCode;
          if (statusCode >= 200 && statusCode < 300) {
            var result;
            try {
              result = JSON.parse(data);
            } catch (e) {
              result = { raw: data };
            }
            var accepted = result.accepted || events.length;
            node.status({ fill: "green", shape: "dot", text: accepted + " accepted" });
            var outMsg = { payload: result };
            sends.forEach(function (s) { s([outMsg, null]); });
          } else {
            var errText = "HTTP " + statusCode + ": " + data.substring(0, 200);
            node.status({ fill: "red", shape: "dot", text: "HTTP " + statusCode });
            var errOutMsg = { payload: { error: errText, statusCode: statusCode } };
            sends.forEach(function (s) { s([null, errOutMsg]); });
          }
          dones.forEach(function (d) { d(); });
        });
      });

      req.on("error", function (err) {
        node.status({ fill: "red", shape: "dot", text: err.message });
        var errOutMsg = { payload: { error: err.message } };
        sends.forEach(function (s) { s([null, errOutMsg]); });
        dones.forEach(function (d) { d(); });
      });

      req.setTimeout(30000, function () {
        req.destroy(new Error("Request timeout"));
      });

      req.write(body);
      req.end();
    }

    node.on("input", function (msg, send, done) {
      send = send || function () { node.send.apply(node, arguments); };
      done = done || function (err) { if (err) node.error(err, msg); };

      try {
        var envelope = typeof msg.payload === "string"
          ? JSON.parse(msg.payload)
          : msg.payload;

        if (!envelope || !envelope.event_type) {
          node.status({ fill: "red", shape: "dot", text: "missing event_type" });
          send([null, { payload: { error: "Payload is not a valid IAES envelope" } }]);
          done();
          return;
        }

        if (batchSize <= 1) {
          buffer.push({ envelope: envelope, msg: msg, send: send, done: done });
          flush();
        } else {
          buffer.push({ envelope: envelope, msg: msg, send: send, done: done });
          if (buffer.length >= batchSize) {
            flush();
          } else if (!timer) {
            timer = setTimeout(flush, batchTimeout);
          }
        }
      } catch (err) {
        node.status({ fill: "red", shape: "dot", text: err.message });
        send([null, { payload: { error: err.message } }]);
        done();
      }
    });

    node.on("close", function () {
      if (timer) { clearTimeout(timer); timer = null; }
      buffer.length = 0;
    });
  }

  RED.nodes.registerType("iaes-publish", IaesPublishNode, {
    credentials: {
      apiKey: { type: "password" },
    },
  });
};
