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
PUBLISHED_EVENT_TYPES = frozenset({
    "asset.measurement",
    "asset.health",
    "asset.hierarchy",
    "sensor.registration",
    "maintenance.work_order_intent",
    "maintenance.completion",
    "maintenance.spare_part_usage",
})


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


def compute_content_hash(data: Dict[str, Any]) -> str:
    """SHA-256 prefix (16 chars) of the data payload for idempotency.

    Args:
        data: The ``data`` dict from an IAES event (None values excluded).

    Returns:
        First 16 hex characters of the SHA-256 digest.
    """
    canonical = json.dumps(
        _normalize_for_hash(data), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
