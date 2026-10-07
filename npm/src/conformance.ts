/**
 * What the schemas annotate and the specification requires.
 *
 * `validate` answers one question: does the schema accept this event? In 2.x
 * the schemas declare `uuid`, `date-time`, `date` and `uri` with `format`,
 * which Draft 2020-12 treats as an annotation, while the specification makes
 * RFC 4122, RFC 3339 and RFC 3986 normative for those fields (IAES_SPEC.md,
 * "An event can be schema-valid and non-conforming"). Making `format` binding
 * in the schema is a narrowing change (GOVERNANCE.md §4.2), so it is not
 * available inside 2.x.
 *
 * `findNonconformities` answers the second question: which fields break what
 * the specification requires? It keeps no list of fields of its own: it reads
 * the `format` annotations from the schemas this package ships, exactly as the
 * Python SDK's `find_nonconformities` does. Both run the shared cases in
 * conformance/validation.json.
 *
 * No optional dependency: unlike `validate`, this does not need ajv.
 */

import * as fs from "fs";
import * as path from "path";

// The mapping of event types to schema files lives in validation.ts, once.
import { schemaFileFor } from "./validation";

const SCHEMA_DIR = path.join(__dirname, "..", "schemas");

const UUID = /^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$/;
const DATE = /^(\d{4})-(\d{2})-(\d{2})$/;
const DATE_TIME =
  /^(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$/;
// RFC 3986 section 3: a scheme, then only unreserved, reserved and
// percent-encoded characters.
const URI =
  /^[A-Za-z][A-Za-z0-9+.\-]*:(?:[A-Za-z0-9\-._~:/?#[\]@!$&'()*+,;=]|%[0-9A-Fa-f]{2})*$/;
// IAES_SPEC.md, producer rule 4: the timestamp MUST be UTC. "-00:00" is not
// UTC in RFC 3339: it means the offset is unknown.
const UTC_DESIGNATORS = new Set(["Z", "z", "+00:00"]);

function isDate(year: string, month: string, day: string): boolean {
  const y = Number(year);
  const m = Number(month);
  const d = Number(day);
  if (m < 1 || m > 12 || d < 1) return false;
  // Date.UTC rolls February 30th over to March; a real date round-trips.
  const t = new Date(Date.UTC(y, m - 1, d));
  return t.getUTCFullYear() === y && t.getUTCMonth() === m - 1 && t.getUTCDate() === d;
}

function dateOk(value: string): boolean {
  const m = DATE.exec(value);
  return m !== null && isDate(m[1], m[2], m[3]);
}

function dateTimeOk(value: string): boolean {
  const m = DATE_TIME.exec(value);
  if (m === null) return false;
  if (!isDate(m[1], m[2], m[3])) return false;
  // RFC 3339 allows a leap second (60).
  if (Number(m[4]) > 23 || Number(m[5]) > 59 || Number(m[6]) > 60) return false;
  return UTC_DESIGNATORS.has(m[8]);
}

const CHECKS: Record<string, (v: string) => boolean> = {
  uuid: (v) => UUID.test(v),
  "date-time": dateTimeOk,
  date: dateOk,
  uri: (v) => URI.test(v),
};

const cache = new Map<string, Record<string, unknown>>();

function schema(filename: string): Record<string, unknown> {
  let s = cache.get(filename);
  if (s === undefined) {
    s = JSON.parse(fs.readFileSync(path.join(SCHEMA_DIR, filename), "utf-8")) as Record<
      string,
      unknown
    >;
    cache.set(filename, s);
  }
  return s;
}

function isObject(v: unknown): v is Record<string, unknown> {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

/** Walk `properties` in step with the instance and check annotated strings. */
function check(node: Record<string, unknown>, value: unknown, at: string, found: string[]): void {
  const fmt = node["format"];
  if (typeof fmt === "string" && fmt in CHECKS && typeof value === "string" && !CHECKS[fmt](value)) {
    found.push(at);
  }
  const props = node["properties"];
  if (isObject(props) && isObject(value)) {
    for (const [key, child] of Object.entries(props)) {
      if (key in value && isObject(child)) {
        check(child, value[key], at ? `${at}.${key}` : key, found);
      }
    }
  }
}

/**
 * The fields of `event` whose value the specification forbids.
 *
 * Returns dotted paths (`"event_id"`, `"data.calibration_date"`), sorted and
 * without duplicates. An empty array means every annotated field conforms.
 * Only string values are judged: a value of the wrong type is the schema's
 * question, and `validate` answers it.
 */
export function findNonconformities(event: unknown): string[] {
  if (!isObject(event)) return [];
  const found: string[] = [];
  check(schema("iaes-envelope.schema.json"), event, "", found);
  const eventType = event["event_type"];
  const filename = typeof eventType === "string" ? schemaFileFor(eventType) : undefined;
  if (filename !== undefined) check(schema(filename), event, "", found);
  // Sorted by UTF-16 code unit, which for these ASCII field names is the same
  // order Python's sorted() gives.
  return Array.from(new Set(found)).sort();
}
