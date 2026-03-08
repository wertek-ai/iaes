/** IAES envelope utilities — content hashing and spec version. */

import { createHash, randomUUID } from "crypto";

export const SPEC_VERSION = "1.2";

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

  if (opts.sourceEventId != null) {
    envelope.source_event_id = opts.sourceEventId;
  }
  if (opts.batchId != null) {
    envelope.batch_id = opts.batchId;
  }

  return envelope;
}
