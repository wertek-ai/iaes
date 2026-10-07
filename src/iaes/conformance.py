"""What the schemas annotate and the specification requires.

``validate`` answers one question: does the schema accept this event? In 2.x
that leaves a gap the specification itself names (IAES_SPEC.md, "An event can
be schema-valid and non-conforming"): the schemas declare ``uuid``,
``date-time``, ``date`` and ``uri`` with ``format``, which Draft 2020-12 treats
as an annotation, while the specification makes RFC 4122, RFC 3339 and
RFC 3986 normative for those fields. Making ``format`` binding in the schema is
a narrowing change (GOVERNANCE.md §4.2), so it is not available inside 2.x.

``find_nonconformities`` answers the second question: which fields break what
the specification requires? It does not keep its own list of fields. It reads
the ``format`` annotations from the schemas this package ships, so a field
that gains an annotation is checked without anyone remembering to add it here
-- a hand-kept list is how four implementations came to disagree.

Stdlib only: unlike ``validate``, this needs no optional dependency.
"""

import datetime
import json
import re
from pathlib import Path
from typing import Any, Dict, List

_SCHEMA_DIR = Path(__file__).parent / "schemas"

_UUID = re.compile(
    r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$"
)
_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_DATE_TIME = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$"
)
# RFC 3986 section 3: a scheme, then only unreserved, reserved and
# percent-encoded characters.
_URI = re.compile(
    r"^[A-Za-z][A-Za-z0-9+.\-]*:(?:[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=]|%[0-9A-Fa-f]{2})*$"
)
# IAES_SPEC.md, producer rule 4: the timestamp MUST be UTC. "-00:00" is not
# UTC in RFC 3339: it means the offset is unknown.
_UTC_DESIGNATORS = ("Z", "z", "+00:00")


def _is_date(year: str, month: str, day: str) -> bool:
    try:
        datetime.date(int(year), int(month), int(day))
    except ValueError:
        return False
    return True


def _date_ok(value: str) -> bool:
    m = _DATE.match(value)
    return bool(m) and _is_date(*m.groups())


def _date_time_ok(value: str) -> bool:
    m = _DATE_TIME.match(value)
    if not m:
        return False
    year, month, day, hour, minute, second, _, offset = m.groups()
    if not _is_date(year, month, day):
        return False
    # RFC 3339 allows a leap second (60).
    if int(hour) > 23 or int(minute) > 59 or int(second) > 60:
        return False
    return offset in _UTC_DESIGNATORS


_CHECKS = {
    "uuid": lambda v: bool(_UUID.match(v)),
    "date-time": _date_time_ok,
    "date": _date_ok,
    "uri": lambda v: bool(_URI.match(v)),
}

_cache: Dict[str, Any] = {}


def _schema(filename: str) -> Dict[str, Any]:
    if filename not in _cache:
        with open(_SCHEMA_DIR / filename, "r", encoding="utf-8") as f:
            _cache[filename] = json.load(f)
    return _cache[filename]


def _check(node: Dict[str, Any], value: Any, path: str, found: List[str]) -> None:
    """Walk ``properties`` in step with the instance and check annotated strings."""
    fmt = node.get("format")
    if fmt in _CHECKS and isinstance(value, str) and not _CHECKS[fmt](value):
        found.append(path)
    props = node.get("properties")
    if isinstance(props, dict) and isinstance(value, dict):
        for key, child in props.items():
            if key in value and isinstance(child, dict):
                _check(child, value[key], f"{path}.{key}" if path else key, found)


def find_nonconformities(event: Dict[str, Any]) -> List[str]:
    """The fields of ``event`` whose value the specification forbids.

    Returns dotted paths (``"event_id"``, ``"data.calibration_date"``), sorted
    and without duplicates. An empty list means every annotated field
    conforms. Only string values are judged: a value of the wrong type is the
    schema's question, and ``validate`` answers it.
    """
    if not isinstance(event, dict):
        return []
    # Import here: validation imports nothing from this module, and the
    # mapping of event types to files lives there, once.
    from .validation import _SCHEMA_FILES

    found: List[str] = []
    _check(_schema("iaes-envelope.schema.json"), event, "", found)
    filename = _SCHEMA_FILES.get(event.get("event_type"))
    if filename:
        _check(_schema(filename), event, "", found)
    return sorted(set(found))
