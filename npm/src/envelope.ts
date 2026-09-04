/** IAES envelope utilities — content hashing and spec version. */

import { createHash, randomUUID } from "crypto";

export const SPEC_VERSION = "1.4";

/**
 * Canonical base for schema identity. Every schema is served at
 * `SCHEMA_BASE + <event_type>`, which is why `dataschema` can be derived
 * instead of asked for: the event type already determines the contract.
 * See GOVERNANCE.md §5.
 */
export const SCHEMA_BASE = "https://iaes.dev/schema/v1/";

/**
 * Event types whose schema is published. `dataschema` is only emitted for
 * these: pointing at a URI that does not resolve is worse than omitting the
 * field, and is the exact defect v1.4 corrected.
 */
export const PUBLISHED_EVENT_TYPES = new Set([
  "asset.measurement",
  "asset.health",
  "asset.hierarchy",
  "sensor.registration",
  "maintenance.work_order_intent",
  "maintenance.completion",
  "maintenance.spare_part_usage",
]);

/** The schema URI for an event type, or undefined if none is published. */
export function schemaUriFor(eventType: string): string | undefined {
  return PUBLISHED_EVENT_TYPES.has(eventType) ? SCHEMA_BASE + eventType : undefined;
}

/** Recursively sort object keys to match Python's json.dumps(sort_keys=True). */
function sortKeys(obj: unknown): unknown {
  if (obj === null || obj === undefined || typeof obj !== "object") return obj;
  if (Array.isArray(obj)) return obj.map(sortKeys);
  const sorted: Record<string, unknown> = {};
  for (const key of Object.keys(obj as Record<string, unknown>).sort()) {
    sorted[key] = sortKeys((obj as Record<string, unknown>)[key]);
  }
  return sorted;
}

/** SHA-256 prefix (16 chars) of the data payload for idempotency. */
export function computeContentHash(data: Record<string, unknown>): string {
  const canonical = JSON.stringify(sortKeys(data));
  return createHash("sha256").update(canonical).digest("hex").slice(0, 16);
}

export function uuid(): string {
  return randomUUID();
}

export interface AssetIdentity {
  asset_id: string;
  asset_name?: string | null;
  plant?: string | null;
  area?: string | null;
}

export interface IAESEnvelope {
  spec_version: string;
  /** Canonical URI of the schema `data` was written against (v1.4). */
  dataschema?: string;
  event_type: string;
  event_id: string;
  correlation_id: string;
  source_event_id?: string;
  batch_id?: string;
  timestamp: string;
  source: string;
  content_hash: string;
  asset: AssetIdentity;
  data: Record<string, unknown>;
}

export function buildEnvelope(opts: {
  eventType: string;
  eventId: string;
  correlationId: string;
  sourceEventId?: string | null;
  batchId?: string | null;
  timestamp: string;
  source: string;
  asset: AssetIdentity;
  data: Record<string, unknown>;
  /** Override the derived schema URI. Pass null to omit it entirely. */
  dataschema?: string | null;
}): IAESEnvelope {
  // Remove null/undefined values from data
  const cleanData: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(opts.data)) {
    if (v != null) cleanData[k] = v;
  }

  const envelope: IAESEnvelope = {
    spec_version: SPEC_VERSION,
    event_type: opts.eventType,
    event_id: opts.eventId,
    correlation_id: opts.correlationId,
    timestamp: opts.timestamp,
    source: opts.source,
    content_hash: computeContentHash(cleanData),
    asset: opts.asset,
    data: cleanData,
  };

  // The event type determines the contract, so the producer gets this for
  // free. `dataschema: null` opts out; anything else overrides the derivation.
  const derived = opts.dataschema === undefined ? schemaUriFor(opts.eventType) : opts.dataschema;
  if (derived != null) {
    envelope.dataschema = derived;
  }

  if (opts.sourceEventId != null) {
    envelope.source_event_id = opts.sourceEventId;
  }
  if (opts.batchId != null) {
    envelope.batch_id = opts.batchId;
  }

  return envelope;
}
