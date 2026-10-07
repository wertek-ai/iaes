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
  if (typeof value === "string") return jcsString(value);
  if (Array.isArray(value)) return "[" + value.map(canonicalJson).join(",") + "]";
  if (typeof value === "object") {
    // Only a plain object is a JSON object. JSON.stringify writes a Map, a Set
    // or a class instance as "{}" (or as whatever its toJSON returns), so two
    // different values would hash the same; refuse instead of guessing.
    const proto = Object.getPrototypeOf(value);
    if (proto !== Object.prototype && proto !== null) {
      const name = (value as object).constructor?.name ?? "object";
      throw new Error(`${name} is not a JSON object; only plain objects can be hashed`);
    }
    const obj = value as Record<string, unknown>;
    const keys = Object.keys(obj).filter((k) => obj[k] !== undefined).sort();
    return "{" + keys.map((k) => jcsString(k) + ":" + canonicalJson(obj[k])).join(",") + "}";
  }
  throw new Error(`${typeof value} is not a JSON value`);
}

// A high surrogate not followed by a low one, or a low one not preceded by a high one.
const LONE_SURROGATE = /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?:^|[^\uD800-\uDBFF])[\uDC00-\uDFFF]/;

function isWellFormed(s: string): boolean {
  const native = (s as unknown as { isWellFormed?: () => boolean }).isWellFormed;
  return typeof native === "function" ? native.call(s) : !LONE_SURROGATE.test(s);
}

/**
 * RFC 8785 serialises I-JSON (RFC 7493), which excludes lone surrogates.
 * JSON.stringify would escape one as `\ud800` and hash it, while an
 * implementation that encodes to UTF-8 cannot; refuse it, as the Python SDK does.
 */
function jcsString(s: string): string {
  if (!isWellFormed(s)) {
    throw new Error("a string with a lone surrogate is not I-JSON (RFC 8785, section 3.1); omit content_hash");
  }
  return JSON.stringify(s);
}

/**
 * The only spec_version form that selects RFC 8785: `2.<minor>`, with the
 * minor read as a number (so `2.10` is later than `2.9`). The same expression
 * is in the Python SDK.
 */
const SPEC_VERSION_2X = /^2\.([0-9]+)$/;

/**
 * IAES-RFC-011 and IAES_SPEC.md, Producer Guidelines, recommended behavior 6.
 *
 * JCS when the event declares `2.<minor>` with minor 1 or later. Anything else
 * -- absent, `2.0`, `3`, `2.1-rc` -- keeps the 2.0 computation: an
 * implementation does not guess the rule of a version it cannot read.
 */
function usesJcs(specVersion: string | null | undefined): boolean {
  if (typeof specVersion !== "string") return false;
  const m = SPEC_VERSION_2X.exec(specVersion);
  return m !== null && parseInt(m[1], 10) >= 1;
}

/**
 * SHA-256 prefix (16 chars) of the data payload for idempotency.
 *
 * The rule follows the `spec_version` the event declares (IAES-RFC-011 §5):
 * `2.<minor>` with minor 1 or later hashes the UTF-8 bytes of the JCS
 * serialisation; anything else -- 2.0 and earlier, an absent `spec_version`
 * (`undefined` or `null` passed explicitly), or a value that is not
 * `2.<minor>` -- keeps the 2.0 computation, so an event built as 2.0 and
 * retried after an upgrade keeps its hash and is not counted twice.
 *
 * Omitting the argument means this SDK's own version (`SPEC_VERSION`).
 * Passing `event.spec_version` from an event that has none means absent, as
 * in the Python SDK, where that value is `None`.
 *
 * @throws Error under RFC 8785, for a value it cannot serialise: NaN, an
 *   infinity (which is also what an integer beyond the largest double parses
 *   to), a lone surrogate, or something that is not a JSON value. The producer
 *   omits `content_hash` (it is optional).
 */
export function computeContentHash(
  data: Record<string, unknown>,
  specVersion?: string | null,
): string {
  // `arguments.length`, not a default parameter: a default would turn an
  // explicitly absent spec_version (undefined) into this SDK's version.
  const declared = arguments.length < 2 ? SPEC_VERSION : specVersion;
  const canonical = usesJcs(declared) ? canonicalJson(data) : JSON.stringify(sortKeys(data));
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
  /**
   * false for `asset.state`, which MUST NOT carry `content_hash`
   * (IAES_SPEC.md, `asset.state`, rule 3): the hash is then not computed at
   * all, so a value RFC 8785 cannot serialise does not fail an event that
   * never needed it. The caller drops the field and returns the wire type.
   */
  withContentHash?: boolean;
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
    content_hash: opts.withContentHash === false ? "" : computeContentHash(cleanData),
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
