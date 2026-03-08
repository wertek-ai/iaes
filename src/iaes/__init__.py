"""IAES — Industrial Asset Event Standard.

A vendor-neutral Python SDK for creating, serializing, and validating
industrial asset events per the IAES v1.2 specification.

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

from .envelope import SPEC_VERSION, compute_content_hash
from .enums import (
    CompletionStatus,
    HierarchyLevel,
    ISO13374Status,
    MeasurementType,
    RegistrationStatus,
    RelationshipType,
    Severity,
    UnitsQualifier,
    WorkOrderPriority,
)
from .models import (
    AssetHealth,
    AssetHierarchy,
    AssetMeasurement,
    MaintenanceCompletion,
    SensorRegistration,
    SparePartUsage,
    WorkOrderIntent,
    from_dict,
)
from .validation import ValidationError, validate, load_schema

__version__ = "0.1.0"

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
    # Enums
    "Severity",
    "MeasurementType",
    "UnitsQualifier",
    "ISO13374Status",
    "WorkOrderPriority",
    "CompletionStatus",
    "HierarchyLevel",
    "RelationshipType",
    "RegistrationStatus",
    # Helpers
    "from_dict",
    "validate",
    "load_schema",
    "compute_content_hash",
    "ValidationError",
]
