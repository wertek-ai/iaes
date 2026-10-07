"""Writes `tags.json`: the reference scenarios as an Ignition tag export.

The scenario IS `tags.json` -- the file an integrator imports into an Ignition
8.3 Gateway. This script only generates it, so the Gateway script stays
readable as Python and is indented exactly as Ignition expects (one tab: the
body of `valueChanged(tag, tagPath, previousValue, currentValue, initialChange,
missedEvents)`). `tests/test_reference_scenarios.py` checks that `tags.json` is
what this script writes.

    python scenarios/ignition/build_tags.py

Ignition is where IAES belongs when the reading already lives in a SCADA/MES
Gateway: the tag is there, and so are the downtime and maintenance screens. The
script uses only the Python standard library and
`system.*`, so it runs on Ignition's Jython 2.7 and, in CI, on CPython.
"""
import json
from pathlib import Path

FOLDER = "IAES_ReferenceStory"

SCRIPT = r'''
# IAES reference scenarios, told by an Ignition Gateway. Set `run` to true: the
# script emits the five events of the story, sends them as ONE batch to
# `receiver_url` (if set), writes them to `last_events` and sets `run` back to
# false. Standard library + system.* only (Jython 2.7 and CPython).
if initialChange or not currentValue.value:
	return
import datetime
import hashlib
import json
import uuid
try:
	# In Jython a Java exception (e.g. java.io.IOException from httpClient) is NOT a Python Exception:
	# `except Exception` lets it escape. Found on a real Gateway; CPython has no `java`, so it falls back.
	from java.lang import Throwable as JavaThrowable
except ImportError:
	JavaThrowable = Exception
log = system.util.getLogger("iaes.reference_story")
root = "[default]__FOLDER__/"
reading, receiver = system.tag.readBlocking([root + "vibration_velocity", root + "receiver_url"])
ASSET = {"asset_id": "MOTOR-001", "asset_name": "Feed Pump Motor", "plant": "North Plant", "area": "Pumping"}
SCHEMA_BASE = "https://iaes.dev/schema/v2/"

def normalize(obj):
	# Whole-number floats hash as integers, as in every other implementation.
	if isinstance(obj, float) and obj == int(obj):
		return int(obj)
	if isinstance(obj, dict):
		return dict((k, normalize(v)) for k, v in obj.items())
	if isinstance(obj, list):
		return [normalize(v) for v in obj]
	return obj

def content_hash(data):
	canonical = json.dumps(normalize(data), sort_keys=True, separators=(",", ":"))
	return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

def stamp():
	return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def published(event_type, source, data, parent=None):
	event = {
		"spec_version": "2.0",
		"event_type": event_type,
		"event_id": str(uuid.uuid4()),
		"correlation_id": parent["correlation_id"] if parent else str(uuid.uuid4()),
		"timestamp": stamp(),
		"source": source,
		"content_hash": content_hash(data),
		"asset": dict(ASSET),
		"data": data,
		"dataschema": SCHEMA_BASE + event_type,
	}
	if parent:
		event["source_event_id"] = parent["event_id"]
	return event

def story():
	if not reading.quality.isGood() or reading.value is None:
		raise ValueError("vibration_velocity has no good-quality value")
	measurement = published("asset.measurement", "sensor.line1", {
		"measurement_type": "vibration_velocity", "value": float(reading.value), "unit": "mm/s",
		"units_qualifier": "rms"})
	health = published("asset.health", "acme.vibration", {
		"health_index": 0.58, "severity": "high", "failure_mode": "bearing_outer_race"}, measurement)
	intent = published("maintenance.work_order_intent", "acme.rule_engine", {
		"title": "Inspect drive-end bearing", "priority": "high",
		"description": "Vibration velocity at 4.2 mm/s RMS with an outer-race signature. "
		               "Inspect the drive-end bearing at the next available window."}, health)
	completion = published("maintenance.completion", "acme.cmms", {
		"work_order_id": "WO-2026-0912", "status": "completed"}, intent)
	# An event type IAES does not publish, in a namespace the producer controls: written by hand, no hash.
	custom = {
		"spec_version": "2.0", "event_type": "acme.press_stroke", "event_id": str(uuid.uuid4()),
		"correlation_id": measurement["correlation_id"], "timestamp": measurement["timestamp"],
		"source": "acme.press_line", "asset": {"asset_id": ASSET["asset_id"]},
		"data": {"strokes": 412, "tonnage_peak": 88.4}}
	return [measurement, health, intent, completion, custom]

def tell():
	try:
		events = story()
		body = json.dumps(events)
		system.tag.writeBlocking([root + "last_events"], [body])
		url = (receiver.value or "").strip() if receiver.quality.isGood() else ""
		if url:
			response = system.net.httpClient(timeout=20000).post(
				url, data=body, headers={"Content-Type": "application/json"})
			log.info("told the story: %d events to %s -> HTTP %s" % (len(events), url, response.statusCode))
		else:
			log.info("told the story: %d events (no receiver_url: written to last_events only)" % len(events))
	except (Exception, JavaThrowable) as e:
		log.error("the story failed: %s" % e)
	finally:
		system.tag.writeBlocking([root + "run"], [False])

system.util.invokeAsynchronous(tell)
'''


def script() -> str:
    body = SCRIPT.strip("\n").replace("__FOLDER__", FOLDER)
    return "\n".join("\t" + line if line else "" for line in body.split("\n"))


def build() -> dict:
    return {
        "name": FOLDER,
        "tagType": "Folder",
        "tags": [
            {"name": "vibration_velocity", "tagType": "AtomicTag", "valueSource": "memory", "dataType": "Float8",
             "value": 4.2, "documentation": "mm/s RMS. In production, point this at your sensor's tag."},
            {"name": "receiver_url", "tagType": "AtomicTag", "valueSource": "memory", "dataType": "String",
             "value": "", "documentation": "Where the batch is POSTed (an IAES receiver). Empty: nothing is sent."},
            {"name": "last_events", "tagType": "AtomicTag", "valueSource": "memory", "dataType": "String",
             "value": "", "documentation": "The five events of the last run, as a JSON list."},
            {"name": "run", "tagType": "AtomicTag", "valueSource": "memory", "dataType": "Boolean", "value": False,
             "documentation": "Set to true to tell the story; the script sets it back to false.",
             "eventScripts": [{"eventid": "valueChanged", "script": script()}]},
        ],
    }


if __name__ == "__main__":
    out = Path(__file__).with_name("tags.json")
    out.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8", newline="\n")
    print("wrote", out)
