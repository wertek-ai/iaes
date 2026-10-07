"""IAES — Industrial Asset Event Standard.

A vendor-neutral Python SDK for creating, serializing, and validating
industrial asset events per the IAES v2.1 specification.

Usage::

    from iaes import AssetMeasurement, AssetHealth, Severity

    # Create a measurement event
    event = AssetMeasurement(
        asset_id="MOTOR-001",
        measurement_type="vibration_velocity",
        value=4.2,
        unit="mm/s",
        source="acme.sensors.plant1",
    )

    # Serialize to IAES wire format
    payload = event.to_dict()

    # Optional: validate against JSON Schema
    from iaes import validate
    validate(payload)  # raises iaes.ValidationError if invalid
"""

from .envelope import SPEC_VERSION, canonical_json, compute_content_hash, schema_uri_for
from .enums import (
    CompletionStatus,
    ConditionTrend,
    DownCause,
    DownKind,
    HierarchyLevel,
    ISO13374Status,
    MeasurementType,
    PreviousState,
    RegistrationStatus,
    RelationshipType,
    Severity,
    UnitsQualifier,
    UpDownState,
    UpMode,
    WorkOrderPriority,
)
from .models import (
    AssetHealth,
    AssetHierarchy,
    AssetMeasurement,
    AssetState,
    MaintenanceCompletion,
    SensorRegistration,
    SparePartUsage,
    WorkOrderIntent,
    from_dict,
    from_object,
)
from .validation import ValidationError, validate, load_schema
from .conformance import find_nonconformities
from ._from_schema import CATALOGS, REQUIRED_DATA_FIELDS
from .client import Client, IaesClientError

# AsyncClient is only available if httpx is installed
try:
    from .client import AsyncClient
except ImportError:
    pass

__version__ = "2.1.0"

__all__ = [
    # Version
    "__version__",
    "SPEC_VERSION",
    # Models
    "AssetMeasurement",
    "AssetHealth",
    "WorkOrderIntent",
    "MaintenanceCompletion",
    "AssetHierarchy",
    "SensorRegistration",
    "SparePartUsage",
    "AssetState",
    # Client
    "Client",
    "AsyncClient",
    "IaesClientError",
    # Enums
    "Severity",
    "MeasurementType",
    "UnitsQualifier",
    "ISO13374Status",
    "ConditionTrend",
    "WorkOrderPriority",
    "CompletionStatus",
    "HierarchyLevel",
    "RelationshipType",
    "RegistrationStatus",
    "UpDownState",
    "DownKind",
    "DownCause",
    "UpMode",
    "PreviousState",
    # Helpers
    "from_object",
    "from_dict",
    "validate",
    "find_nonconformities",
    "CATALOGS",
    "REQUIRED_DATA_FIELDS",
    "load_schema",
    "compute_content_hash",
    "canonical_json",
    "schema_uri_for",
    "ValidationError",
]
