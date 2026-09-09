/**
 * IAES schema validation — optional dependency on `ajv`.
 *
 * Install with: `npm install ajv`
 *
 * This is the capability `surface.json` requires of a library claiming the
 * IAES SDK profile, and the one this SDK did not have. It mirrors the Python
 * SDK deliberately: the same behaviour, the same shape of failure, the same
 * treatment of a custom `event_type` — because the point of the profile is
 * that somebody who has learned one has learned them all.
 */

import * as fs from "fs";
import * as path from "path";

const SCHEMA_DIR = path.join(__dirname, "..", "schemas");

/** Map event_type to schema filename. */
const SCHEMA_FILES: Record<string, string> = {
  "asset.measurement": "asset-measurement.schema.json",
  "asset.health": "asset-health.schema.json",
  "maintenance.work_order_intent": "maintenance-work-order-intent.schema.json",
  "maintenance.completion": "maintenance-completion.schema.json",
  "asset.hierarchy": "asset-hierarchy.schema.json",
  "sensor.registration": "sensor-registration.schema.json",
  "maintenance.spare_part_usage": "maintenance-spare-part-usage.schema.json",
};

const schemaCache = new Map<string, Record<string, unknown>>();

/** Raised when an IAES event fails schema validation. */
export class ValidationError extends Error {
  readonly errors: string[];

  constructor(message: string, errors: string[] = []) {
    super(message);
    this.name = "ValidationError";
    this.errors = errors;
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

function readSchema(filename: string): Record<string, unknown> {
  const cached = schemaCache.get(filename);
  if (cached) return cached;

  const schema = JSON.parse(
    fs.readFileSync(path.join(SCHEMA_DIR, filename), "utf-8"),
  ) as Record<string, unknown>;
  schemaCache.set(filename, schema);
  return schema;
}

/**
 * Load a bundled JSON schema by IAES event type.
 *
 * @throws Error if the event_type has no corresponding schema.
 */
export function loadSchema(eventType: string): Record<string, unknown> {
  const filename = SCHEMA_FILES[eventType];
  if (filename === undefined) {
    throw new Error(`No schema for event_type: ${JSON.stringify(eventType)}`);
  }
  return readSchema(filename);
}

/** Load the IAES envelope schema. */
export function loadEnvelopeSchema(): Record<string, unknown> {
  return readSchema("iaes-envelope.schema.json");
}

interface AjvLike {
  compile(schema: unknown): {
    (data: unknown): boolean;
    errors?: Array<{ instancePath: string; message?: string }> | null;
  };
  addSchema(schema: unknown, key?: string): unknown;
}

function loadAjv(): AjvLike {
  let Ajv2020: new (options: Record<string, unknown>) => AjvLike;
  try {
    // Draft 2020-12, which is the dialect every IAES schema declares.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const mod = require("ajv/dist/2020");
    Ajv2020 = (mod.default ?? mod) as typeof Ajv2020;
  } catch {
    throw new Error(
      "Schema validation requires ajv. Install with: npm install ajv",
    );
  }
  // `format` is an annotation in Draft 2020-12, not an assertion, so ajv
  // reports that it ignores "date-time" every time a schema compiles. That
  // behaviour is correct and deliberate: asserting `format` would make this
  // SDK stricter than the standard and reject events the Python SDK accepts,
  // which is worse than not checking it. Making `format` binding is a
  // narrowing change under GOVERNANCE.md §4.2 and belongs in its own memo.
  //
  // The one known message is dropped and everything else is forwarded: a
  // logger set to `false` would also hide a warning nobody has seen yet.
  const logger = {
    log: (...args: unknown[]) => console.log(...args),
    warn: (...args: unknown[]) => {
      if (/unknown format/.test(String(args[0]))) return;
      console.warn(...args);
    },
    error: (...args: unknown[]) => console.error(...args),
  };
  return new Ajv2020({ allErrors: true, strict: false, logger });
}

function report(
  eventType: string,
  errors: Array<{ instancePath: string; message?: string }>,
): never {
  // The path first, because the profile requires reporting the path of the
  // offending field, and because a message without one sends a reader looking.
  const lines = errors
    .slice(0, 10)
    .map((e) => `  - ${e.instancePath || "$"}: ${e.message ?? "invalid"}`);
  throw new ValidationError(
    `IAES validation failed for '${eventType}' ` +
      `(${errors.length} error(s)):\n${lines.join("\n")}`,
    errors.map((e) => `${e.instancePath || "$"}: ${e.message ?? "invalid"}`),
  );
}

/**
 * Validate an IAES event against its JSON schema.
 *
 * A custom `event_type` with no published schema is validated against the
 * envelope alone: everything the standard governs is still checked, and only
 * `data` is left unjudged, because there is nothing to judge it against. An
 * unknown type is not an invalid event.
 *
 * @throws ValidationError if the event does not conform.
 * @throws Error if `ajv` is not installed.
 */
export function validate(input: unknown): void {
  // `unknown`, not `Record<string, unknown>`: a validator must be able to
  // receive something whose shape is not yet known to be valid. The narrower
  // type rejected the SDK's OWN envelope -- IAESEnvelope has no index
  // signature -- so `validate(buildEnvelope(...))` did not compile, and the
  // most obvious path through this library needed a cast. It also rejected the
  // result of JSON.parse without one. Widening a parameter is compatible:
  // every call that compiled before still compiles.
  if (input === null || typeof input !== "object" || Array.isArray(input)) {
    throw new ValidationError("Event must be a JSON object");
  }
  const event = input as Record<string, unknown>;

  const ajv = loadAjv();

  const eventType = event["event_type"];
  if (typeof eventType !== "string" || eventType === "") {
    throw new ValidationError("Missing 'event_type' field");
  }

  const envelopeSchema = loadEnvelopeSchema();

  // Membership, not exceptions. An earlier version wrapped loadSchema in a
  // bare `catch`, which caught every failure -- a missing file, corrupt JSON,
  // an unreadable disk -- and degraded a PUBLISHED type to envelope-only. That
  // turns a fault in the SDK into permissiveness in the contract: a broken
  // asset.health schema would have meant every asset.health payload passes.
  //
  // Only "this type has no published schema" takes the custom path. Any real
  // failure below propagates, which is what the Python SDK does by raising
  // ValueError for the unmapped case alone.
  if (SCHEMA_FILES[eventType] === undefined) {
    const check = ajv.compile(envelopeSchema);
    if (!check(event)) {
      const errors = check.errors ?? [];
      const lines = errors
        .slice(0, 10)
        .map((e) => `  - ${e.instancePath || "$"}: ${e.message ?? "invalid"}`);
      throw new ValidationError(
        `Envelope validation failed (${errors.length} error(s)):\n` +
          lines.join("\n"),
        errors.map((e) => `${e.instancePath || "$"}: ${e.message ?? "invalid"}`),
      );
    }
    return;
  }

  const eventSchema = loadSchema(eventType);

  // Event schemas carry a relative $ref to "iaes-envelope.schema.json", which
  // resolves against the event schema's own $id base -- not against the
  // envelope's $id, which ends in "/envelope". Register it under both so the
  // reference resolves whichever way ajv asks for it.
  const eventId = String(eventSchema["$id"] ?? "");
  const base = eventId.includes("/")
    ? eventId.slice(0, eventId.lastIndexOf("/") + 1)
    : "";
  ajv.addSchema(envelopeSchema, String(envelopeSchema["$id"] ?? ""));
  if (base) ajv.addSchema(envelopeSchema, `${base}iaes-envelope.schema.json`);

  const check = ajv.compile(eventSchema);
  if (!check(event)) report(eventType, check.errors ?? []);
}
