"""IAES envelope utilities — content hashing and spec version constant."""

import hashlib
import json
from typing import Any, Dict

SPEC_VERSION = "2.0"

#: Canonical base for schema identity. Every schema is served at
#: ``SCHEMA_BASE + <event_type>``, which is why ``dataschema`` can be derived
#: instead of asked for: the event type already determines the contract.
#: See GOVERNANCE.md section 5.
SCHEMA_BASE = "https://iaes.dev/schema/v2/"

#: Event types whose schema is published. ``dataschema`` is only emitted for
#: these: pointing at a URI that does not resolve is worse than omitting the
#: field, and is the exact defect v1.4 corrected.
#: Generated from schema/ (tools/generate_from_schema.py), never written here.
from ._from_schema import PUBLISHED_EVENT_TYPES  # noqa: E402


def schema_uri_for(event_type: str):
    """The schema URI for an event type, or ``None`` if none is published."""
    return SCHEMA_BASE + event_type if event_type in PUBLISHED_EVENT_TYPES else None


def _normalize_for_hash(obj: Any) -> Any:
    """Normalize values for cross-language hash compatibility.

    Converts whole-number floats to int so Python's ``25600.0`` matches
    JavaScript's ``25600`` in JSON serialization.
    """
    if isinstance(obj, float) and obj.is_integer():
        return int(obj)
    if isinstance(obj, dict):
        return {k: _normalize_for_hash(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_for_hash(v) for v in obj]
    return obj


_SHORT_ESCAPES = {'"': '\\"', "\\": "\\\\", "\b": "\\b", "\f": "\\f", "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def _jcs_string(s: str) -> str:
    """RFC 8785 §3.2.2.2: escape only `"`, `\\` and control characters; everything else as is."""
    out = ['"']
    for ch in s:
        if ch in _SHORT_ESCAPES:
            out.append(_SHORT_ESCAPES[ch])
        elif ord(ch) < 0x20:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _jcs_number(x) -> str:
    """RFC 8785 §3.2.2.3: the ECMAScript Number.prototype.toString form of an IEEE-754 double.

    Python's repr already gives the shortest digits that round-trip, which is what
    ECMAScript uses; only the placement of the decimal point and the exponent form
    differ, so the digits are taken from repr and laid out by the ECMAScript rule.
    """
    from decimal import Decimal

    if isinstance(x, int):
        if abs(x) > 2 ** 53:
            raise ValueError("an integer beyond 2**53 has no exact JSON number form; omit content_hash")
        x = float(x)
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError("NaN and Infinity have no JSON form; omit content_hash")
    if x == 0:
        return "0"  # also -0
    sign = "-" if x < 0 else ""
    d = Decimal(repr(abs(x))).normalize()
    digits = "".join(map(str, d.as_tuple().digits))
    k = len(digits)
    n = d.as_tuple().exponent + k  # value = 0.digits x 10^n
    if k <= n <= 21:
        body = digits + "0" * (n - k)
    elif 0 < n <= 21:
        body = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        body = "0." + "0" * (-n) + digits
    else:
        e = n - 1
        body = digits[0] + ("." + digits[1:] if k > 1 else "") + "e" + ("+" if e >= 0 else "-") + str(abs(e))
    return sign + body


def canonical_json(value: Any) -> str:
    """The RFC 8785 (JCS) serialisation of a JSON value (IAES-RFC-011)."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _jcs_string(value)
    if isinstance(value, (int, float)):
        return _jcs_number(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(canonical_json(v) for v in value) + "]"
    if isinstance(value, dict):
        # Members sorted by their names as UTF-16 code units, not code points.
        keys = sorted(value, key=lambda k: k.encode("utf-16-be"))
        return "{" + ",".join(_jcs_string(k) + ":" + canonical_json(value[k]) for k in keys) + "}"
    raise TypeError(f"{type(value).__name__} is not a JSON value")


def _usa_jcs(spec_version: str) -> bool:
    """IAES-RFC-011: events that declare 2.1 or later hash by JCS; earlier ones keep their rule."""
    try:
        major, minor = (int(p) for p in str(spec_version).split(".")[:2])
    except ValueError:
        return False
    return (major, minor) >= (2, 1)


def compute_content_hash(data: Dict[str, Any], spec_version: str = SPEC_VERSION) -> str:
    """SHA-256 prefix (16 chars) of the data payload for idempotency.

    The rule follows the ``spec_version`` the event declares (IAES-RFC-011, §5):
    2.1 and later hash the UTF-8 bytes of the RFC 8785 (JCS) serialisation; 2.0
    and earlier keep the 2.0 computation, so an event built as 2.0 and retried
    after an upgrade keeps its hash and is not counted twice.

    Args:
        data: The ``data`` dict from an IAES event (None values excluded).
        spec_version: The version the event declares. Defaults to this SDK's.

    Returns:
        First 16 hex characters of the SHA-256 digest.
    """
    if _usa_jcs(spec_version):
        return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()[:16]
    canonical = json.dumps(
        _normalize_for_hash(data), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
