"""IAES envelope utilities — content hashing and spec version constant."""

import hashlib
import json
from typing import Any, Dict

SPEC_VERSION = "1.2"


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
