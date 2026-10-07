/** IAES envelope utilities — content hashing and spec version. */

import { createHash, randomUUID } from "crypto";

export const SPEC_VERSION = "2.1";

/**
 * Canonical base for schema identity. Every schema is served at
 * `SCHEMA_BASE + <event_type>`, which is why `dataschema` can be derived
 * instead of asked for: the event type already determines the contract.
 * See GOVERNANCE.md §5.
 */
export const SCHEMA_BASE = "https://iaes.dev/schema/v2/";

/**
 * Event types whose schema is published. `dataschema` is only emitted for
 * these: pointing at a URI that does not resolve is worse than omitting the
 * field, and is the exact defect v1.4 corrected.
 */
// Generated from schema/ (tools/generate_from_schema.py), never written here.
import { PUBLISHED_EVENT_TYPES } from "./fromSchema";
export { PUBLISHED_EVENT_TYPES };

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

/**
 * The RFC 8785 (JCS) serialisation of a JSON value (IAES-RFC-011).
 *
 * Strings and numbers are exactly what `JSON.stringify` writes (RFC 8785 is
 * defined in those terms). Object members are written in sorted order HERE,
 * rather than by building a sorted object: JavaScript enumerates integer-like
 * keys first, in numeric order, whatever order they were inserted in, so
 * `{"9":1,"10":2}` came out with "9" first. JCS sorts by UTF-16 code unit,
 * which is what `Array.prototype.sort` does on strings: "10" before "9".
 */
export function canonicalJson(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new Error("NaN and Infinity have no JSON form; omit content_hash");
    }
    return JSON.stringify(value);
  }
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(canonicalJson).join(",") + "]";
  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    const keys = Object.keys(obj).filter((k) => obj[k] !== undefined).sort();
    return "{" + keys.map((k) => JSON.stringify(k) + ":" + canonicalJson(obj[k])).join(",") + "}";
  }
  throw new Error(`${typeof value} is not a JSON value`);
}

/** IAES-RFC-011: events that declare 2.1 or later hash by JCS; earlier ones keep their rule. */
function usesJcs(specVersion: string): boolean {
  const [major, minor] = String(specVersion).split(".").map((p) => parseInt(p, 10));
  if (Number.isNaN(major) || Number.isNaN(minor)) return false;
  return major > 2 || (major === 2 && minor >= 1);
}

/**
 * SHA-256 prefix (16 chars) of the data payload for idempotency.
 *
 * The rule follows the `spec_version` the event declares (IAES-RFC-011 §5):
 * 2.1 and later hash the UTF-8 bytes of the JCS serialisation; 2.0 and earlier
 * keep the 2.0 computation, so an event built as 2.0 and retried after an
 * upgrade keeps its hash and is not counted twice.
 */
export function computeContentHash(
  data: Record<string, unknown>,
  specVersion: string = SPEC_VERSION,
): string {
  const canonical = usesJcs(specVersion) ? canonicalJson(data) : JSON.stringify(sortKeys(data));
  return createHash("sha256").update(canonical, "utf8").digest("hex").slice(0, 16);
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
  /**
   * Always present on an envelope this SDK produced.
   *
   * It stays REQUIRED here, and the reason is compatibility rather than the
   * schema: `IAESEnvelope` is what every `toJSON()` returns, so weakening it
   * to optional breaks code that already compiles --
   * `event.content_hash.slice(0, 8)` becomes an error on a value the SDK
   * always sets. GOVERNANCE.md 3.1 forbids a package making a breaking API
   * change without the specification advancing, and 2.0.1 is a platform
   * release.
   *
   * The wire contract is looser: `iaes-envelope.schema.json` does not list
   * `content_hash` in `required`, so an envelope that omits it conforms. That
   * shape is `IAESWireEnvelope`, below.
   */
  content_hash: string;
  asset: AssetIdentity;
  data: Record<string, unknown>;
}

/**
 * An envelope as it may arrive ON THE WIRE, rather than as this SDK builds one.
 *
 * Two differences, and they are the only two. Measured by comparing every
 * property of `iaes-envelope.schema.json` against this interface, rather than
 * fixing them one at a time as they are noticed:
 *
 *   content_hash      the schema does not list it in `required`, so a
 *                     conforming producer may omit it. `IAESEnvelope` keeps it
 *                     required because every `toJSON()` sets it and code that
 *                     already reads it must keep compiling.
 *   source_event_id   the schema types it `["string", "null"]`, so an explicit
 *                     null may appear on the wire. The specification assigns
 *                     no meaning to it beyond that -- it says the field
 *                     references the originating event -- so neither does this
 *                     type. `IAESEnvelope` stays `string | undefined` because
 *                     this SDK omits the field rather than emitting null.
 *
 * `tests/test_wire_type_matches_schema.py` keeps that list honest.
 *
 * Two types because there are two contracts, and collapsing them means either
 * breaking existing code or lying about what an event must carry.
 *
 * `validate()` accepts both -- it takes `unknown`.
 */
export type IAESWireEnvelope = Omit<
  IAESEnvelope,
  "content_hash" | "source_event_id"
> & {
  content_hash?: string;
  source_event_id?: string | null;
};

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
