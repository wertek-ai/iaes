#!/usr/bin/env python3
"""Build the shared conformance cases in conformance/.

IAES has one specification and four implementations -- the Python SDK, the
TypeScript SDK, the Node-RED nodes and the n8n nodes -- and until this suite
each of them re-wrote the rules by hand. Measured on 2026-10-06, that is how
they came to disagree:

  - Node-RED accepted spec_version "205" (a regex built from a JS string
    turned "\\." into ".") while Python rejected it;
  - n8n's strict mode kept its own list of required fields, missing
    asset.hierarchy and three fields the schemas require;
  - Node-RED rejected events with a non-UUID event_id that every other
    validator accepts, because only it checked the format;
  - Python and TypeScript computed different content_hash values for six of
    eleven payloads.

A suite of cases that every implementation runs makes agreement something
CI measures instead of something a reviewer hopes for.

The expected values are written here literally, from the specification and
the schemas, and are NOT computed by calling any implementation: a suite whose
answers come from the code it judges cannot fail. The only thing computed is
the SHA-256 of a canonical string that is itself written out by hand.

Stdlib only, like the other tools in this directory.

  python tools/build_conformance_cases.py           # write conformance/*.json
  python tools/build_conformance_cases.py --check   # fail if they are stale
"""

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "conformance"

EVENT_ID = "7c9e6679-7425-40de-944b-e07fc1f90ae7"
CORRELATION_ID = "9b2a3f4e-1c5d-4e6f-8a7b-0c1d2e3f4a5b"


def envelope(event_type, data, **overrides):
    event = {
        "spec_version": "2.0",
        "event_type": event_type,
        "event_id": EVENT_ID,
        "correlation_id": CORRELATION_ID,
        "timestamp": "2026-10-06T12:00:00Z",
        "source": "acme.monitoring",
        "asset": {"asset_id": "PUMP-101"},
        "data": data,
    }
    event.update(overrides)
    return event


# One minimal event per published type: only what its schema requires.
MINIMAL = {
    "asset.measurement": {"measurement_type": "vibration_velocity", "value": 4.2, "unit": "mm/s"},
    "asset.health": {"health_index": 0.58, "severity": "high"},
    "asset.hierarchy": {"hierarchy_level": "equipment", "relationship_type": "child_of"},
    "sensor.registration": {"sensor_id": "SENSOR-7", "registration_status": "registered"},
    "maintenance.work_order_intent": {"title": "Inspect bearing", "priority": "high"},
    "maintenance.completion": {"status": "completed", "work_order_id": "WO-1"},
    "maintenance.spare_part_usage": {"work_order_id": "WO-1", "spare_part_id": "BRG-6205", "quantity_used": 1},
}


def state_event(data, **overrides):
    """An asset.state event. The type is published from 2.1 (IAES-RFC-010), so it declares 2.1."""
    return envelope("asset.state", data, **{"spec_version": "2.1", **overrides})


def minimal(event_type, **overrides):
    return envelope(event_type, copy.deepcopy(MINIMAL[event_type]), **overrides)


def without(event, *path):
    event = copy.deepcopy(event)
    node = event
    for key in path[:-1]:
        node = node[key]
    del node[path[-1]]
    return event


def with_data(event_type, **fields):
    event = minimal(event_type)
    event["data"].update(fields)
    return event


def validation_cases():
    cases = []

    def case(case_id, title, event, schema_valid, nonconforming=()):
        cases.append({
            "id": case_id,
            "title": title,
            "event": event,
            "expect": {
                "schema_valid": schema_valid,
                # An event the schema rejects does not conform either, and its
                # fields are not judged one by one: there is nothing to judge.
                "conforming": schema_valid and not nonconforming,
                "nonconforming_fields": sorted(nonconforming) if schema_valid else [],
            },
        })

    # -- Valid and conforming ------------------------------------------------
    for event_type in MINIMAL:
        case(f"valid.{event_type}", f"minimal {event_type}: only what its schema requires",
             minimal(event_type), True)
    case("valid.custom_event_type",
         "an event_type IAES does not publish, in a namespace the producer controls: the catalogue is open",
         envelope("acme.press_stroke", {"stroke_mm": 120}), True)
    case("valid.custom_event_type_any_data",
         "a custom type's data is not judged: there is no schema to judge it against",
         envelope("acme.press_stroke", {}), True)
    case("valid.extra_envelope_field",
         "an unknown envelope field is carried, not rejected",
         minimal("asset.health", x_vendor_note="kept"), True)
    case("valid.source_event_id_null", "source_event_id may be null",
         minimal("asset.health", source_event_id=None), True)
    case("valid.dataschema", "dataschema carries a URI",
         minimal("asset.health", dataschema="https://iaes.dev/schema/v2/asset.health"), True)
    case("valid.timestamp_offset_zero", "UTC written as +00:00 is UTC",
         minimal("asset.health", timestamp="2026-10-06T12:00:00+00:00"), True)
    case("valid.timestamp_fraction", "fractional seconds are RFC 3339",
         minimal("asset.health", timestamp="2026-10-06T12:00:00.123Z"), True)
    case("valid.calibration_date", "calibration_date is an RFC 3339 full-date",
         with_data("sensor.registration", calibration_date="2026-03-05"), True)
    case("valid.spec_version_later_minor", "a later 2.x minor is the same major",
         minimal("asset.health", spec_version="2.7"), True)

    # -- Rejected by the schema ---------------------------------------------
    case("schema.event_not_an_object", "an event is a JSON object; a validator reports, it does not crash",
         [minimal("asset.health")], False)
    case("schema.spec_version_without_dot", "spec_version \"205\" is not major.minor",
         minimal("asset.health", spec_version="205"), False)
    case("schema.spec_version_other_major", "a 1.x event is not validated by the 2.x schemas",
         minimal("asset.health", spec_version="1.4"), False)
    case("schema.spec_version_major_only", "spec_version needs a minor",
         minimal("asset.health", spec_version="2"), False)
    for field in ("spec_version", "event_type", "event_id", "correlation_id",
                  "timestamp", "source", "asset", "data"):
        case(f"schema.missing_{field}", f"{field} is required",
             without(minimal("asset.health"), field), False)
    case("schema.event_type_uppercase", "event_type is lowercase dot-notation",
         envelope("Asset.Health", copy.deepcopy(MINIMAL["asset.health"])), False)
    case("schema.event_type_without_namespace", "event_type needs a namespace",
         envelope("health", {}), False)
    case("schema.source_with_space", "source is lowercase dot-notation",
         minimal("asset.health", source="Acme Monitoring"), False)
    case("schema.asset_without_id", "asset.asset_id is required",
         minimal("asset.health", asset={"name": "Pump"}), False)
    case("schema.data_is_array", "data is an object",
         envelope("acme.press_stroke", []), False)
    case("schema.content_hash_too_short", "content_hash is exactly 16 characters",
         minimal("asset.health", content_hash="0123456789abcde"), False)
    case("schema.measurement_value_string", "a measurement's value is a number",
         with_data("asset.measurement", value="4.2"), False)
    for event_type, field in (
        ("asset.measurement", "unit"),
        ("asset.health", "severity"),
        ("asset.hierarchy", "hierarchy_level"),
        ("sensor.registration", "registration_status"),
        ("maintenance.work_order_intent", "priority"),
        ("maintenance.completion", "status"),
        ("maintenance.spare_part_usage", "work_order_id"),
    ):
        case(f"schema.{event_type}.missing_{field}", f"{event_type} requires data.{field}",
             without(minimal(event_type), "data", field), False)
    case("schema.asset.hierarchy.empty_data", "asset.hierarchy with empty data",
         envelope("asset.hierarchy", {}), False)
    case("schema.health_index_null", "a required number is not null",
         with_data("asset.health", health_index=None), False)
    case("schema.health_index_out_of_range", "health_index is between 0 and 1",
         with_data("asset.health", health_index=1.5), False)
    case("schema.severity_not_in_catalogue", "severity is one of the published values",
         with_data("asset.health", severity="urgent"), False)

    # -- asset.state (2.1, IAES-RFC-010) ------------------------------------
    # Declared once per transition. down_cause and up_mode are OPEN: an unknown
    # value is "not classified", never an error. content_hash is FORBIDDEN: data
    # carries no time, so two identical trips would hash the same and the second
    # would be dropped as a duplicate.
    case("valid.asset.state", "minimal asset.state: only what its schema requires",
         state_event({"state": "up"}), True)
    case("valid.asset.state.trip", "a trip: down, unplanned, an other unplanned outage",
         state_event({"state": "down", "down_kind": "unplanned", "down_cause": "other_unplanned",
                      "previous_state": "up", "detail": "trip"}), True)
    case("valid.asset.state.unknown_down_cause", "down_cause is open: an unpublished cause is not classified, not invalid",
         state_event({"state": "down", "down_kind": "planned", "down_cause": "acme_shift_change"}), True)
    case("valid.asset.state.unknown_up_mode", "up_mode is open: an unpublished mode is not classified, not invalid",
         state_event({"state": "up", "up_mode": "acme_jog"}), True)
    case("valid.asset.state.previous_unknown", "a producer that starts without knowing the previous state says so",
         state_event({"state": "up", "up_mode": "running", "previous_state": "unknown"}), True)
    case("schema.asset.state.content_hash", "asset.state carries no content_hash",
         state_event({"state": "up"}, content_hash="0123456789abcdef"), False)
    case("schema.asset.state.missing_state", "asset.state requires data.state",
         state_event({"previous_state": "up"}), False)
    case("schema.asset.state.state_not_in_catalogue", "state is up or down",
         state_event({"state": "stopped"}), False)
    case("schema.asset.state.down_without_kind", "a down state says whether it is planned",
         state_event({"state": "down", "down_cause": "other_unplanned"}), False)
    case("schema.asset.state.cause_disagrees_with_kind", "a published down_cause agrees with down_kind",
         state_event({"state": "down", "down_kind": "planned", "down_cause": "corrective_maintenance"}), False)

    # -- Accepted by the schema, not conforming to the specification ---------
    # In 2.x the schemas only ANNOTATE these formats (Draft 2020-12), and
    # making them binding is a narrowing change (GOVERNANCE.md §4.2). The
    # specification still requires them (IAES_SPEC.md, "References"). So the
    # validator says valid, and a conformance check names the field.
    case("nonconforming.event_id", "event_id must be a UUID (RFC 4122)",
         minimal("asset.health", event_id="no-uuid"), True, ["event_id"])
    case("nonconforming.event_id_almost_uuid", "a non-hex digit makes it not a UUID",
         minimal("asset.health", event_id="h1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c"), True, ["event_id"])
    case("nonconforming.correlation_id", "correlation_id must be a UUID",
         minimal("asset.health", correlation_id="PUMP-101:bearing_outer_race"), True, ["correlation_id"])
    case("nonconforming.source_event_id", "source_event_id, when present, must be a UUID",
         minimal("asset.health", source_event_id="example-001"), True, ["source_event_id"])
    case("nonconforming.timestamp_not_a_date", "timestamp must be RFC 3339",
         minimal("asset.health", timestamp="banana"), True, ["timestamp"])
    case("nonconforming.timestamp_without_offset", "timestamp must carry a timezone designator",
         minimal("asset.health", timestamp="2026-10-06T12:00:00"), True, ["timestamp"])
    case("nonconforming.timestamp_not_utc",
         "timestamp must be UTC (IAES_SPEC.md producer rule 4), even though +02:00 is valid RFC 3339",
         minimal("asset.health", timestamp="2026-10-06T14:00:00+02:00"), True, ["timestamp"])
    case("nonconforming.timestamp_impossible_date", "February 30th is not a date",
         minimal("asset.health", timestamp="2026-02-30T12:00:00Z"), True, ["timestamp"])
    case("nonconforming.dataschema", "dataschema must be a URI (RFC 3986)",
         minimal("asset.health", dataschema="esto no es uri"), True, ["dataschema"])
    case("nonconforming.calibration_date", "calibration_date must be an RFC 3339 full-date",
         with_data("sensor.registration", calibration_date="05/03/2026"), True, ["data.calibration_date"])
    case("nonconforming.two_fields", "every nonconforming field is named, not only the first",
         minimal("asset.health", event_id="no-uuid", timestamp="banana"), True, ["event_id", "timestamp"])
    return cases


def sha16(canonical):
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def hash_cases():
    """content_hash vectors.

    `agreed` cases: every implementation must produce exactly these bytes.
    `divergent_2_0` cases: the 2.0 implementations disagree, and this records
    what each produces so the disagreement stays MEASURED. If an
    implementation stops matching its recorded value, the runner fails: either
    the divergence was fixed (move the case to agreed) or it changed (which is
    worse). The fix is proposed as a draft RFC: RFC 8785, JCS (wertek-ai/iaes#57).
    """
    agreed = [
        ("ascii", "plain ASCII payload",
         {"measurement_type": "vibration_velocity", "value": 4.2, "unit": "mm/s"},
         '{"measurement_type":"vibration_velocity","unit":"mm/s","value":4.2}'),
        ("whole_float", "25600.0 hashes as 25600 in both languages",
         {"value": 25600.0, "unit": "Hz"},
         '{"unit":"Hz","value":25600}'),
        ("nested", "keys are sorted at every depth; arrays keep their order",
         {"b": {"y": [3, 2, 1], "x": True}, "a": "z"},
         '{"a":"z","b":{"x":true,"y":[3,2,1]}}'),
        ("empty", "empty data",
         {}, "{}"),
        ("negative_zero", "-0.0 is written as 0",
         {"value": -0.0}, '{"value":0}'),
    ]
    divergent = [
        ("non_ascii", "Python escapes non-ASCII characters; TypeScript writes them as UTF-8",
         {"reason": "disparo de protección"},
         '{"reason":"disparo de protecci\\u00f3n"}',
         '{"reason":"disparo de protección"}'),
        ("astral", "a character outside the BMP: escaped surrogates vs UTF-8",
         {"note": "\U0001F527 wrench"},
         '{"note":"\\ud83d\\udd27 wrench"}',
         '{"note":"\U0001F527 wrench"}'),
        ("integer_like_keys", "JavaScript enumerates integer-like keys first, in numeric order",
         {"9": 1, "10": 2, "a": 3},
         '{"10":2,"9":1,"a":3}',
         '{"9":1,"10":2,"a":3}'),
        ("small_exponent", "Python writes 1e-07; JavaScript writes 1e-7",
         {"value": 1e-7},
         '{"value":1e-07}',
         '{"value":1e-7}'),
        ("large_whole_float", "Python turns 1e21 into an integer; JavaScript writes 1e+21",
         {"value": 1e21},
         '{"value":1000000000000000000000}',
         '{"value":1e+21}'),
        ("key_order_outside_bmp", "Python sorts keys by code point; JavaScript by UTF-16 code unit",
         {"": 1, "\U0001F600": 2},
         '{"\\ue000":1,"\\ud83d\\ude00":2}',
         '{"\U0001F600":2,"":1}'),
    ]
    out = []
    # RFC 8785 (JCS), the rule of 2.1 and later (IAES-RFC-011). Written out by hand
    # from RFC 8785: members sorted by UTF-16 code unit, strings unescaped except
    # `"`, backslash and control characters, numbers as ECMAScript writes them.
    # Characters outside ASCII are built with chr() so that no tool on the way can
    # rewrite an escape sequence in this source.
    bs, q = chr(92), chr(34)
    jcs = {
        "ascii": '{"measurement_type":"vibration_velocity","unit":"mm/s","value":4.2}',
        "whole_float": '{"unit":"Hz","value":25600}',
        "nested": '{"a":"z","b":{"x":true,"y":[3,2,1]}}',
        "empty": "{}",
        "negative_zero": '{"value":0}',
        "non_ascii": '{"reason":"disparo de protecci' + chr(0xF3) + 'n"}',
        "astral": '{"note":"' + chr(0x1F527) + ' wrench"}',
        "integer_like_keys": '{"10":2,"9":1,"a":3}',
        "small_exponent": '{"value":1e-7}',
        "large_whole_float": '{"value":1e+21}',
        "key_order_outside_bmp": "{" + q + chr(0x1F600) + q + ":2," + q + chr(0xE000) + q + ":1}",
    }
    for case_id, title, data, canonical in agreed:
        out.append({"id": case_id, "title": title, "data": data, "status": "agreed",
                    "canonical": canonical, "content_hash": sha16(canonical),
                    "jcs": {"canonical": jcs[case_id], "content_hash": sha16(jcs[case_id])}})
    for case_id, title, data, py, ts in divergent:
        out.append({"id": case_id, "title": title, "data": data, "status": "divergent_2_0",
                    "by_implementation": {
                        "python": {"canonical": py, "content_hash": sha16(py)},
                        "typescript": {"canonical": ts, "content_hash": sha16(ts)},
                    },
                    "jcs": {"canonical": jcs[case_id], "content_hash": sha16(jcs[case_id])}})

    # Cases that exist only for JCS: RFC 8785's own example (§3.2.4) and the
    # boundaries of the ECMAScript number form.
    rfc_string_value = chr(0x20AC) + "$" + chr(0x0F) + chr(0x0A) + "A'B" + q + bs + bs + q + "/"
    rfc_string_jcs = (q + chr(0x20AC) + "$" + bs + "u000f" + bs + "n" + "A'B" + bs + q
                      + bs + bs + bs + bs + bs + q + "/" + q)
    solo_jcs = [
        ("rfc8785_example", "RFC 8785 section 3.2.4, verbatim",
         {"numbers": [333333333.33333329, 1e30, 4.50, 2e-3, 1e-27],
          "string": rfc_string_value, "literals": [None, True, False]},
         '{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],"string":'
         + rfc_string_jcs + "}"),
        ("number_boundaries", "where ECMAScript switches to exponent form: 1e20 and 1e-6 stay plain; 1e21 and 1e-7 do not",
         {"a": 1e20, "b": 1e21, "c": 0.000001, "d": 1e-7, "e": -1.5e-5},
         '{"a":100000000000000000000,"b":1e+21,"c":0.000001,"d":1e-7,"e":-0.000015}'),
        ("control_characters", "control characters: short forms where they exist, \\u00xx otherwise",
         {"s": "a" + chr(8) + chr(9) + chr(10) + chr(12) + chr(13) + chr(7) + "z"},
         '{"s":"a' + bs + "b" + bs + "t" + bs + "n" + bs + "f" + bs + "r" + bs + 'u0007z"}'),
    ]
    for case_id, title, data, canonical in solo_jcs:
        out.append({"id": case_id, "title": title, "data": data, "status": "jcs_only",
                    "jcs": {"canonical": canonical, "content_hash": sha16(canonical)}})
    return out


def documents():
    note = ("Generated by tools/build_conformance_cases.py; edit the generator, not this file. "
            "See conformance/README.md.")
    return {
        "validation.json": {"$comment": note, "spec_version": "2.0", "cases": validation_cases()},
        "content_hash.json": {"$comment": note, "spec_version": "2.0", "cases": hash_cases()},
    }


def render(doc):
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if conformance/*.json is stale")
    args = ap.parse_args()
    stale = []
    for name, doc in documents().items():
        path = OUT / name
        text = render(doc)
        if args.check:
            current = path.read_text(encoding="utf-8") if path.exists() else None
            if current != text:
                stale.append(name)
        else:
            OUT.mkdir(exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    if stale:
        print(f"stale: {stale}. Run python tools/build_conformance_cases.py", file=sys.stderr)
        sys.exit(1)
    if not args.check:
        print("wrote conformance/validation.json and conformance/content_hash.json")


if __name__ == "__main__":
    main()
