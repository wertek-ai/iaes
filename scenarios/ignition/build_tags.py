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

# content_hash for IAES 2.1 (IAES-RFC-011): SHA-256 of the UTF-8 bytes of the RFC 8785
# (JCS) serialisation of data, first 16 hex. json.dumps is not JCS (it escapes non-ASCII,
# writes 1e-07, sorts by code point), so the serialisation is written out here. The same
# code runs on Jython 2.7 and on CPython 3, hence TEXT and INTEGERS.
try:
	TEXT = unicode
	INTEGERS = (int, long)
except NameError:
	TEXT = str
	INTEGERS = (int,)

SHORT = {u'"': u'\\"', u'\\': u'\\\\', u'\b': u'\\b', u'\f': u'\\f', u'\n': u'\\n', u'\r': u'\\r', u'\t': u'\\t'}

def as_text(s):
	if isinstance(s, TEXT):
		return s
	return s.decode("utf-8")

def well_formed(s):
	# RFC 8785 serialises I-JSON, which has no lone surrogates. Jython stores text as UTF-16, so a
	# character outside the BMP arrives here as a high + low pair, and a pair is fine; CPython 3 never
	# pairs them, so there any surrogate is lone (and UnicodeEncodeError, a ValueError, would follow).
	i = 0
	n = len(s)
	while i < n:
		c = ord(s[i])
		if 0xD800 <= c <= 0xDBFF and i + 1 < n and 0xDC00 <= ord(s[i + 1]) <= 0xDFFF:
			i += 2
			continue
		if 0xD800 <= c <= 0xDFFF:
			raise ValueError("a lone surrogate is not I-JSON (RFC 8785, section 3.1)")
		i += 1
	return s

def jcs_string(s):
	# Only the quote, the backslash and control characters are escaped; everything else as is.
	out = [u'"']
	for ch in well_formed(as_text(s)):
		if ch in SHORT:
			out.append(SHORT[ch])
		elif ord(ch) < 0x20:
			out.append(u"\\u%04x" % ord(ch))
		else:
			out.append(ch)
	out.append(u'"')
	return u"".join(out)

def jcs_number(x):
	# The ECMAScript form: the shortest round-trip digits, laid out as ECMAScript does.
	from decimal import Decimal
	if isinstance(x, INTEGERS):
		# RFC 8785 works on IEEE-754 doubles: an integer is the double nearest to it, as JSON.parse
		# reads it (2**53 + 1 hashes as 2**53). Only one beyond the largest double has no form.
		try:
			x = float(x)
		except OverflowError:
			raise ValueError("an integer beyond the largest IEEE-754 double has no JSON form")
	if x != x or x in (float("inf"), float("-inf")):
		raise ValueError("NaN and Infinity have no JSON form")
	if x == 0:
		return u"0"
	sign = u"-" if x < 0 else u""
	# Not repr: in Jython it is Java's Double.toString, which is not the shortest form (1e23 comes out
	# as 9.999999999999999e+22, 5e-324 as 4.9e-324; measured on a Gateway, 2026-10-07). The fewest
	# correctly rounded digits that read back as the same double are the shortest, in any Python.
	for p in range(1, 18):
		shortest = "%.*e" % (p - 1, abs(x))
		if float(shortest) == abs(x):
			break
	t = Decimal(shortest).normalize().as_tuple()
	digits = u"".join([TEXT(d) for d in t.digits])
	k = len(digits)
	n = t.exponent + k
	if k <= n <= 21:
		body = digits + u"0" * (n - k)
	elif 0 < n <= 21:
		body = digits[:n] + u"." + digits[n:]
	elif -6 < n <= 0:
		body = u"0." + u"0" * (-n) + digits
	else:
		e = n - 1
		body = digits[0] + (u"." + digits[1:] if k > 1 else u"") + u"e" + (u"+" if e >= 0 else u"-") + TEXT(abs(e))
	return sign + body

def canonical(v):
	if v is None:
		return u"null"
	if v is True:
		return u"true"
	if v is False:
		return u"false"
	if isinstance(v, (TEXT, str)):
		return jcs_string(v)
	if isinstance(v, INTEGERS) or isinstance(v, float):
		return jcs_number(v)
	if isinstance(v, (list, tuple)):
		return u"[" + u",".join([canonical(i) for i in v]) + u"]"
	if isinstance(v, dict):
		# Members sorted by their names as UTF-16 code units, not code points (checked first: the
		# sort key cannot encode a lone surrogate).
		keys = sorted(v.keys(), key=lambda key: well_formed(as_text(key)).encode("utf-16-be"))
		return u"{" + u",".join([jcs_string(key) + u":" + canonical(v[key]) for key in keys]) + u"}"
	raise TypeError("not a JSON value: %r" % (v,))

def content_hash(data):
	return hashlib.sha256(canonical(data).encode("utf-8")).hexdigest()[:16]

def stamp():
	return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def published(event_type, source, data, parent=None):
	event = {
		"spec_version": "2.1",
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
		"spec_version": "2.1", "event_type": "acme.press_stroke", "event_id": str(uuid.uuid4()),
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
			# A refused batch is a failure, not a story told: the line says which.
			if 200 <= response.statusCode < 300:
				log.info("told the story: %d events to %s -> HTTP %s" % (len(events), url, response.statusCode))
			else:
				log.error("the receiver refused the story: %d events to %s -> HTTP %s" % (len(events), url, response.statusCode))
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
             "value": 4.2, "documentation": "mm/s RMS. A reference scenario: only this value is read, and the rest "
                              "of the story (severity, work order, its completion) is fixed text. Do not point "
                              "receiver_url at a production system."},
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
