/**
 * IAES Client — generic HTTP client for publishing events to any IAES-compliant endpoint.
 *
 * This module is part of the IAES open standard SDK. It does NOT assume any specific
 * backend implementation. The URL and authentication method are user-configured.
 *
 * @example
 * ```ts
 * import { IaesClient, AssetMeasurement } from "@iaes/sdk";
 *
 * const client = new IaesClient("https://your-iaes-endpoint.example.com", {
 *   apiKey: "your-key",
 * });
 *
 * const event = new AssetMeasurement({
 *   asset_id: "MOTOR-001",
 *   measurement_type: "vibration_velocity",
 *   value: 4.2,
 *   unit: "mm/s",
 *   source: "acme.sensors.plant1",
 * });
 *
 * const result = await client.publish(event);
 * ```
 */

/** Options for the IAES client. */
export interface IaesClientOptions {
  /** API key for authentication (sent as X-API-Key header). */
  apiKey?: string;
  /** Request timeout in milliseconds (default 30000). */
  timeout?: number;
  /** Additional headers to include in every request. */
  headers?: Record<string, string>;
  /** Override the default ingest path (default "/api/v1/iaes/ingest"). */
  ingestPath?: string;
}

/** Response from the ingest endpoint. */
export interface IngestResponse {
  accepted: number;
  rejected: number;
  results: Array<{
    event_id: string;
    status: "stored" | "duplicate" | "error";
    routed_to?: string;
    error?: string;
  }>;
}

/** Error thrown when the IAES endpoint returns an error. */
export class IaesClientError extends Error {
  public readonly statusCode: number;
  public readonly body: string;

  constructor(message: string, statusCode: number = 0, body: string = "") {
    super(message);
    this.name = "IaesClientError";
    this.statusCode = statusCode;
    this.body = body;
  }
}

/** Any IAES event model that has a toJSON() method. */
interface Publishable {
  toJSON(): Record<string, unknown>;
}

/**
 * IAES event publisher. Works with any IAES-compliant ingest endpoint.
 *
 * Uses the Fetch API (Node 18+ or browser). For older runtimes,
 * polyfill fetch or use the Node-RED `iaes-publish` node instead.
 */
export class IaesClient {
  private readonly endpoint: string;
  private readonly apiKey: string;
  private readonly timeout: number;
  private readonly extraHeaders: Record<string, string>;

  constructor(url: string, options: IaesClientOptions = {}) {
    const baseUrl = url.replace(/\/+$/, "");
    const ingestPath = options.ingestPath || "/api/v1/iaes/ingest";
    this.endpoint = baseUrl + ingestPath;
    this.apiKey = options.apiKey || "";
    this.timeout = options.timeout || 30000;
    this.extraHeaders = options.headers || {};
  }

  /**
   * Publish a single IAES event.
   *
   * @param event An IAES model instance (has `toJSON()`) or a raw object.
   * @returns Response from the endpoint.
   */
  async publish(event: Publishable | Record<string, unknown>): Promise<IngestResponse> {
    const envelope = "toJSON" in event && typeof event.toJSON === "function"
      ? event.toJSON()
      : event;
    return this._send(envelope);
  }

  /**
   * Publish a batch of IAES events in a single request (max 100).
   *
   * @param events Array of IAES model instances or raw objects.
   * @returns Response from the endpoint.
   */
  async publishBatch(events: Array<Publishable | Record<string, unknown>>): Promise<IngestResponse> {
    const envelopes = events.map((e) =>
      "toJSON" in e && typeof e.toJSON === "function" ? e.toJSON() : e
    );
    return this._send(envelopes);
  }

  private async _send(payload: unknown): Promise<IngestResponse> {
    const headers: Record<string, string> = {
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
        throw new IaesClientError(
          `HTTP ${response.status}: ${text.substring(0, 500)}`,
          response.status,
          text,
        );
      }

      return JSON.parse(text) as IngestResponse;
    } catch (err) {
      if (err instanceof IaesClientError) throw err;
      const message = err instanceof Error ? err.message : String(err);
      throw new IaesClientError(`Connection failed: ${message}`);
    } finally {
      clearTimeout(timer);
    }
  }
}

/**
 * Convenience function to publish a single event.
 *
 * @param url Base URL of the IAES-compliant endpoint.
 * @param event IAES model instance or raw dict.
 * @param apiKey Optional API key.
 */
export async function publish(
  url: string,
  event: Publishable | Record<string, unknown>,
  apiKey?: string,
): Promise<IngestResponse> {
  const client = new IaesClient(url, { apiKey });
  return client.publish(event);
}
