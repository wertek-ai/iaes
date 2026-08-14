module.exports = function (RED) {
  const https = require("https");
  const http = require("http");

  // Servers implementing the IAES ingest API accept at most 100 envelopes
  // per POST. Sending more gets the WHOLE batch rejected with 422, so the
  // node caps locally instead of letting a misconfigured batch size silently
  // discard everything.
  const MAX_BATCH = 100;
  const DEFAULT_PATH = "/iaes/ingest";

  function IaesPublishNode(config) {
    RED.nodes.createNode(this, config);
    const node = this;

    const requestedBatch = parseInt(config.batchSize, 10) || 1;
    const batchSize = Math.min(Math.max(requestedBatch, 1), MAX_BATCH);
    if (requestedBatch > MAX_BATCH) {
      node.warn(
        "Batch Size " + requestedBatch + " exceeds the IAES limit of " +
        MAX_BATCH + "; using " + MAX_BATCH
      );
    }

    const batchTimeout = (parseFloat(config.batchTimeout) || 5) * 1000;
    const ingestPath = (config.path || DEFAULT_PATH).trim();
    const authScheme = config.authScheme || "apikey";

    const buffer = [];
    let timer = null;
    let inFlight = null;

    function buildOptions(endpoint, body) {
      const parsed = new URL(endpoint);
      const apiKey = (node.credentials && node.credentials.apiKey) || "";

      const headers = {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(body),
      };

      if (apiKey) {
        // IAES ingest authenticates with X-API-Key. Bearer is offered for
        // servers that front the ingest with a JWT gateway.
        if (authScheme === "bearer") {
          headers["Authorization"] = "Bearer " + apiKey;
        } else {
          headers["X-API-Key"] = apiKey;
        }
      }

      return {
        options: {
          hostname: parsed.hostname,
          port: parsed.port || (parsed.protocol === "https:" ? 443 : 80),
          path: parsed.pathname + parsed.search,
          method: "POST",
          headers: headers,
        },
        transport: parsed.protocol === "https:" ? https : http,
      };
    }

    // Count events the server refused because they arrived faster than the
    // asset's registered cadence. Backpressure is not a failure — surfacing
    // it as a generic error would send integrators hunting for a bug.
    function countCadenceDrops(result) {
      if (!result || !Array.isArray(result.results)) return 0;
      return result.results.filter(function (r) {
        return r && r.status === "dropped" && r.reason === "cadence_gate";
      }).length;
    }

    function settle(batch, okMsgFactory, errMsg) {
      batch.forEach(function (item) {
        if (errMsg) {
          item.send([null, Object.assign({}, item.msg, { payload: errMsg })]);
        } else {
          item.send([Object.assign({}, item.msg, { payload: okMsgFactory() }), null]);
        }
        item.done();
      });
    }

    function flush() {
      if (timer) { clearTimeout(timer); timer = null; }
      if (buffer.length === 0) return Promise.resolve();

      const batch = buffer.splice(0, buffer.length);
      const events = batch.map(function (item) { return item.envelope; });

      const targetUrl = config.url;
      if (!targetUrl) {
        const errText = "No URL configured";
        node.status({ fill: "red", shape: "dot", text: errText });
        settle(batch, null, { error: errText });
        return Promise.resolve();
      }

      let endpoint;
      let built;
      const body = JSON.stringify(events.length === 1 ? events[0] : events);
      try {
        endpoint = targetUrl.replace(/\/+$/, "") +
          (ingestPath.charAt(0) === "/" ? ingestPath : "/" + ingestPath);
        built = buildOptions(endpoint, body);
      } catch (err) {
        node.status({ fill: "red", shape: "dot", text: "bad URL" });
        settle(batch, null, { error: "Invalid URL: " + err.message });
        return Promise.resolve();
      }

      const promise = new Promise(function (resolve) {
        const req = built.transport.request(built.options, function (res) {
          let data = "";
          res.on("data", function (chunk) { data += chunk; });
          res.on("end", function () {
            const statusCode = res.statusCode;
            let result;
            try {
              result = JSON.parse(data);
            } catch (e) {
              result = { raw: data };
            }

            if (statusCode >= 200 && statusCode < 300) {
              const accepted = result.accepted != null ? result.accepted : events.length;
              const dropped = countCadenceDrops(result);
              node.status({
                fill: dropped ? "yellow" : "green",
                shape: "dot",
                text: dropped
                  ? accepted + " accepted, " + dropped + " over cadence"
                  : accepted + " accepted",
              });
              settle(batch, function () { return result; }, null);
            } else {
              const dropped = countCadenceDrops(result);
              if (dropped === events.length) {
                // Every event was backpressure, not an error.
                node.status({
                  fill: "yellow", shape: "dot",
                  text: dropped + " over cadence",
                });
              } else {
                node.status({ fill: "red", shape: "dot", text: "HTTP " + statusCode });
              }
              settle(batch, null, {
                error: "HTTP " + statusCode + ": " + data.substring(0, 200),
                statusCode: statusCode,
                cadence_dropped: dropped,
                response: result,
              });
            }
            resolve();
          });
        });

        let settled = false;
        req.on("error", function (err) {
          if (settled) return;
          settled = true;
          node.status({ fill: "red", shape: "dot", text: err.message });
          settle(batch, null, { error: err.message });
          resolve();
        });

        req.setTimeout(30000, function () {
          req.destroy(new Error("Request timeout"));
        });

        req.write(body);
        req.end();
      });

      inFlight = promise;
      promise.then(function () { if (inFlight === promise) inFlight = null; });
      return promise;
    }

    node.on("input", function (msg, send, done) {
      send = send || function () { node.send.apply(node, arguments); };
      done = done || function (err) { if (err) node.error(err, msg); };

      try {
        const envelope = typeof msg.payload === "string"
          ? JSON.parse(msg.payload)
          : msg.payload;

        if (!envelope || !envelope.event_type) {
          node.status({ fill: "red", shape: "dot", text: "missing event_type" });
          send([null, Object.assign({}, msg, {
            payload: { error: "Payload is not a valid IAES envelope" },
          })]);
          done();
          return;
        }

        buffer.push({ envelope: envelope, msg: msg, send: send, done: done });

        if (buffer.length >= batchSize) {
          flush();
        } else if (!timer) {
          timer = setTimeout(flush, batchTimeout);
        }
      } catch (err) {
        node.status({ fill: "red", shape: "dot", text: err.message });
        send([null, Object.assign({}, msg, { payload: { error: err.message } })]);
        done();
      }
    });

    // Deploying or restarting used to discard whatever was still buffered —
    // silently, and without completing the pending messages. Flush first.
    node.on("close", function (done) {
      if (timer) { clearTimeout(timer); timer = null; }
      const finish = typeof done === "function" ? done : function () {};
      const pending = flush();
      Promise.race([
        Promise.all([pending, inFlight].filter(Boolean)),
        new Promise(function (resolve) { setTimeout(resolve, 5000); }),
      ]).then(finish, finish);
    });
  }

  RED.nodes.registerType("iaes-publish", IaesPublishNode, {
    credentials: {
      apiKey: { type: "password" },
    },
  });
};
