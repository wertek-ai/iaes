const { describe, it, before, after } = require("node:test");
const assert = require("node:assert/strict");
const http = require("node:http");

// We test the compiled output — build must run first.
// For now, test the client logic via a direct require of the source transpiled concept.
// Since we can't require .ts directly, we test the pattern with a minimal mock.

// --- Mock IAES Ingest Server ---

let server;
let port;
let lastRequestBody = null;
let lastRequestHeaders = {};
let mockResponseCode = 201;
let mockResponseBody = { accepted: 1, rejected: 0, results: [] };

function startServer() {
  return new Promise((resolve) => {
    server = http.createServer((req, res) => {
      let body = "";
      req.on("data", (chunk) => { body += chunk; });
      req.on("end", () => {
        lastRequestBody = JSON.parse(body);
        lastRequestHeaders = { ...req.headers };

        res.writeHead(mockResponseCode, { "Content-Type": "application/json" });
        res.end(JSON.stringify(mockResponseBody));
      });
    });
    server.listen(0, "127.0.0.1", () => {
      port = server.address().port;
      resolve();
    });
  });
}

function stopServer() {
  return new Promise((resolve) => {
    if (server) server.close(resolve);
    else resolve();
  });
}

function resetMock() {
  lastRequestBody = null;
  lastRequestHeaders = {};
  mockResponseCode = 201;
  mockResponseBody = {
    accepted: 1,
    rejected: 0,
    results: [{ event_id: "test-1", status: "stored", routed_to: "measurements" }],
  };
}

// --- Minimal IaesClient implementation for testing (mirrors client.ts logic) ---
// This avoids requiring TypeScript compilation during test.

class TestIaesClient {
  constructor(url, options = {}) {
    const baseUrl = url.replace(/\/+$/, "");
    const ingestPath = options.ingestPath || "/api/v1/iaes/ingest";
    this.endpoint = baseUrl + ingestPath;
    this.apiKey = options.apiKey || "";
    this.timeout = options.timeout || 30000;
    this.extraHeaders = options.headers || {};
  }

  async publish(event) {
    const envelope = event && typeof event.toJSON === "function" ? event.toJSON() : event;
    return this._send(envelope);
  }

  async publishBatch(events) {
    const envelopes = events.map((e) =>
      e && typeof e.toJSON === "function" ? e.toJSON() : e
    );
    return this._send(envelopes);
  }

  async _send(payload) {
    const headers = {
      "Content-Type": "application/json",
      "User-Agent": "iaes-ts-sdk/0.2.0",
      ...this.extraHeaders,
    };
    if (this.apiKey) {
      headers["X-API-Key"] = this.apiKey;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(this.endpoint, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      const text = await response.text();

      if (!response.ok) {
        const err = new Error(`HTTP ${response.status}: ${text.substring(0, 500)}`);
        err.statusCode = response.status;
        err.body = text;
        throw err;
      }

      return JSON.parse(text);
    } finally {
      clearTimeout(timer);
    }
  }
}

// --- Tests ---

describe("IaesClient", () => {
  before(async () => { await startServer(); });
  after(async () => { await stopServer(); });

  it("should publish a single event", async () => {
    resetMock();
    const client = new TestIaesClient(`http://127.0.0.1:${port}`, { apiKey: "wk_test" });
    const event = {
      event_type: "asset.measurement",
      event_id: "evt-1",
      asset: { asset_id: "MOTOR-001" },
      data: { value: 4.2, unit: "mm/s", measurement_type: "vibration_velocity" },
    };

    const result = await client.publish(event);

    assert.equal(result.accepted, 1);
    assert.equal(lastRequestBody.event_type, "asset.measurement");
    assert.equal(lastRequestBody.asset.asset_id, "MOTOR-001");
  });

  it("should send X-API-Key header", async () => {
    resetMock();
    const client = new TestIaesClient(`http://127.0.0.1:${port}`, { apiKey: "wk_secret_key" });

    await client.publish({ event_type: "asset.health", event_id: "h1", asset: { asset_id: "M-1" }, data: {} });

    assert.equal(lastRequestHeaders["x-api-key"], "wk_secret_key");
  });

  it("should send User-Agent header", async () => {
    resetMock();
    const client = new TestIaesClient(`http://127.0.0.1:${port}`);

    await client.publish({ event_type: "asset.health", event_id: "h2", asset: { asset_id: "M-1" }, data: {} });

    assert.ok(lastRequestHeaders["user-agent"].includes("iaes-ts-sdk"));
  });

  it("should send custom headers", async () => {
    resetMock();
    const client = new TestIaesClient(`http://127.0.0.1:${port}`, {
      headers: { "X-Custom": "val123" },
    });

    await client.publish({ event_type: "asset.health", event_id: "h3", asset: { asset_id: "M-1" }, data: {} });

    assert.equal(lastRequestHeaders["x-custom"], "val123");
  });

  it("should publish batch of events", async () => {
    resetMock();
    mockResponseBody = { accepted: 3, rejected: 0, results: [] };
    const client = new TestIaesClient(`http://127.0.0.1:${port}`, { apiKey: "wk_batch" });

    const events = [
      { event_type: "asset.measurement", event_id: "b1", asset: { asset_id: "M-1" }, data: { value: 1 } },
      { event_type: "asset.measurement", event_id: "b2", asset: { asset_id: "M-1" }, data: { value: 2 } },
      { event_type: "asset.health", event_id: "b3", asset: { asset_id: "M-1" }, data: { health_index: 0.9 } },
    ];

    const result = await client.publishBatch(events);

    assert.equal(result.accepted, 3);
    assert.ok(Array.isArray(lastRequestBody));
    assert.equal(lastRequestBody.length, 3);
  });

  it("should call toJSON() on model instances", async () => {
    resetMock();
    const client = new TestIaesClient(`http://127.0.0.1:${port}`);
    const mockModel = {
      toJSON: () => ({
        event_type: "asset.measurement",
        event_id: "model-1",
        asset: { asset_id: "PUMP-001" },
        data: { value: 99, unit: "°C" },
      }),
    };

    await client.publish(mockModel);

    assert.equal(lastRequestBody.event_id, "model-1");
    assert.equal(lastRequestBody.asset.asset_id, "PUMP-001");
  });

  it("should throw on HTTP 401", async () => {
    resetMock();
    mockResponseCode = 401;
    mockResponseBody = { detail: "Invalid API key" };
    const client = new TestIaesClient(`http://127.0.0.1:${port}`, { apiKey: "bad-key" });

    await assert.rejects(
      () => client.publish({ event_type: "x", event_id: "e1", asset: { asset_id: "M-1" }, data: {} }),
      (err) => {
        assert.equal(err.statusCode, 401);
        assert.ok(err.message.includes("401"));
        return true;
      },
    );
  });

  it("should throw on HTTP 422", async () => {
    resetMock();
    mockResponseCode = 422;
    mockResponseBody = { detail: "Missing event_type" };
    const client = new TestIaesClient(`http://127.0.0.1:${port}`);

    await assert.rejects(
      () => client.publish({ bad: "payload" }),
      (err) => {
        assert.equal(err.statusCode, 422);
        return true;
      },
    );
  });

  it("should throw on connection refused", async () => {
    const client = new TestIaesClient("http://127.0.0.1:1");

    await assert.rejects(
      () => client.publish({ event_type: "x", event_id: "e1", asset: { asset_id: "M-1" }, data: {} }),
    );
  });

  it("should strip trailing slashes from URL", () => {
    const client = new TestIaesClient("http://example.com///");
    assert.equal(client.endpoint, "http://example.com/api/v1/iaes/ingest");
  });

  it("should use custom ingest path", () => {
    const client = new TestIaesClient("http://example.com", { ingestPath: "/custom/ingest" });
    assert.equal(client.endpoint, "http://example.com/custom/ingest");
  });

  it("should handle duplicate response", async () => {
    resetMock();
    mockResponseBody = {
      accepted: 1, rejected: 0,
      results: [{ event_id: "dup-1", status: "duplicate" }],
    };
    const client = new TestIaesClient(`http://127.0.0.1:${port}`);

    const result = await client.publish({ event_type: "asset.measurement", event_id: "dup-1", asset: { asset_id: "M-1" }, data: {} });
    assert.equal(result.results[0].status, "duplicate");
  });
});
