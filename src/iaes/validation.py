"""IAES schema validation — optional dependency on ``jsonschema``.

Install with: ``pip install iaes[validate]``
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

_SCHEMA_DIR = Path(__file__).parent / "schemas"

# Map event_type to schema filename
_SCHEMA_FILES = {
    "asset.measurement": "asset-measurement.schema.json",
    "asset.health": "asset-health.schema.json",
    "maintenance.work_order_intent": "maintenance-work-order-intent.schema.json",
    "maintenance.completion": "maintenance-completion.schema.json",
    "asset.hierarchy": "asset-hierarchy.schema.json",
    "sensor.registration": "sensor-registration.schema.json",
    "maintenance.spare_part_usage": "maintenance-spare-part-usage.schema.json",
}

_schema_cache: Dict[str, Any] = {}


class ValidationError(Exception):
    """Raised when an IAES event fails schema validation."""

    def __init__(self, message: str, errors: Optional[list] = None):
        super().__init__(message)
        self.errors = errors or []


def load_schema(event_type: str) -> Dict[str, Any]:
    """Load a bundled JSON schema by IAES event type.

    Args:
        event_type: E.g. ``"asset.measurement"`` or ``"asset.health"``.

    Returns:
        The parsed JSON schema dict.

    Raises:
        ValueError: If the event_type has no corresponding schema.
    """
    if event_type in _schema_cache:
        return _schema_cache[event_type]

    filename = _SCHEMA_FILES.get(event_type)
    if filename is None:
        raise ValueError(f"No schema for event_type: {event_type!r}")

    schema_path = _SCHEMA_DIR / filename
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    _schema_cache[event_type] = schema
    return schema


def load_envelope_schema() -> Dict[str, Any]:
    """Load the IAES envelope schema."""
    if "__envelope__" in _schema_cache:
        return _schema_cache["__envelope__"]

    schema_path = _SCHEMA_DIR / "iaes-envelope.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    _schema_cache["__envelope__"] = schema
    return schema


def validate(event: Dict[str, Any]) -> None:
    """Validate an IAES event dict against its JSON schema.

    Requires ``jsonschema`` and ``referencing`` to be installed
    (``pip install iaes[validate]``).

    Args:
        event: An IAES wire-format dict (the full envelope).

    Raises:
        ValidationError: If the event does not conform to the schema.
        ImportError: If ``jsonschema`` is not installed.
    """
    try:
        import jsonschema
        from referencing import Registry, Resource
    except ImportError:
        raise ImportError(
            "Schema validation requires jsonschema and referencing. "
            "Install with: pip install iaes[validate]"
        )

    event_type = event.get("event_type")
    if not event_type:
        raise ValidationError("Missing 'event_type' field")

    # Load all schemas for the registry (event schemas reference envelope)
    envelope_schema = load_envelope_schema()
    try:
        event_schema = load_schema(event_type)
    except ValueError as e:
        raise ValidationError(str(e))

    # Build a registry so $ref resolution works.
    # Event schemas use relative $ref "iaes-envelope.schema.json" which
    # resolves against the event schema's $id base URL.
    envelope_resource = Resource.from_contents(envelope_schema)
    event_resource = Resource.from_contents(event_schema)

    # The event schema $id is like https://iaes.wertek.ai/schema/v1/asset.measurement
    # The relative ref resolves to https://iaes.wertek.ai/schema/v1/iaes-envelope.schema.json
    event_id = event_schema.get("$id", "")
    base_url = event_id.rsplit("/", 1)[0] + "/" if "/" in event_id else ""
    resolved_envelope_ref = base_url + "iaes-envelope.schema.json"

    resources = [
        (envelope_schema.get("$id", ""), envelope_resource),
        (event_id, event_resource),
        (resolved_envelope_ref, envelope_resource),
    ]

    registry = Registry().with_resources(resources)

    validator = jsonschema.Draft202012Validator(
        event_schema,
        registry=registry,
    )

    errors = list(validator.iter_errors(event))
    if errors:
        messages = [f"  - {e.json_path}: {e.message}" for e in errors[:10]]
        raise ValidationError(
            f"IAES validation failed for '{event_type}' "
            f"({len(errors)} error(s)):\n" + "\n".join(messages),
            errors=[str(e) for e in errors],
        )
