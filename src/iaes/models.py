"""IAES event models — 7 vendor-neutral dataclasses for the IAES v1.2 spec.

Each model produces a spec-compliant IAES envelope via ``to_dict()``.
All fields are spec-only — no vendor-specific extensions.
"""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

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


def _enum_val(v: Any) -> Any:
    """Extract ``.value`` from enum instances, pass through others."""
    return v.value if hasattr(v, "value") else v


def _parse_timestamp(ts: str) -> datetime:
    """Parse ISO 8601 timestamp, handling 'Z' suffix for Python 3.9/3.10."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid4() -> str:
    return str(uuid.uuid4())


# ─── Shared helpers ─────────────────────────────────────────


def _build_envelope(
    event_type: str,
    *,
    event_id: str,
    correlation_id: str,
    source_event_id: Optional[str],
    batch_id: Optional[str],
    timestamp: datetime,
    source: str,
    asset_id: str,
    asset_name: Optional[str],
    plant: Optional[str],
    area: Optional[str],
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a spec-compliant IAES envelope dict."""
    clean_data = {k: v for k, v in data.items() if v is not None}
    envelope: Dict[str, Any] = {
        "spec_version": SPEC_VERSION,
        "event_type": event_type,
        "event_id": event_id,
        "correlation_id": correlation_id,
        "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp),
        "source": source,
        "content_hash": compute_content_hash(clean_data),
        "asset": {
            "asset_id": asset_id,
            "asset_name": asset_name,
            "plant": plant,
            "area": area,
        },
        "data": clean_data,
    }
    if source_event_id is not None:
        envelope["source_event_id"] = source_event_id
    if batch_id is not None:
        envelope["batch_id"] = batch_id
    return envelope


# ─── asset.measurement ──────────────────────────────────────


@dataclass
class AssetMeasurement:
    """IAES ``asset.measurement`` — a physical sensor reading."""

    asset_id: str
    measurement_type: Union[str, MeasurementType]
    value: float
    unit: str
    source: str = "sensors"

    # Position / channel
    sensor_id: Optional[str] = None
    location: Optional[str] = None

    # ISO 17359 (v1.2)
    units_qualifier: Optional[Union[str, UnitsQualifier]] = None
    sampling_rate_hz: Optional[float] = None
    acquisition_duration_s: Optional[float] = None

    # Asset identity
    asset_name: Optional[str] = None
    plant: Optional[str] = None
    area: Optional[str] = None

    # Envelope
    event_id: str = field(default_factory=_uuid4)
    correlation_id: str = field(default_factory=_uuid4)
    source_event_id: Optional[str] = None
    batch_id: Optional[str] = None
    timestamp: datetime = field(default_factory=_utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to an IAES wire-format dict."""
        data = {
            "measurement_type": _enum_val(self.measurement_type),
            "value": self.value,
            "unit": self.unit,
            "sensor_id": self.sensor_id,
            "location": self.location,
            "units_qualifier": _enum_val(self.units_qualifier) if self.units_qualifier else None,
            "sampling_rate_hz": self.sampling_rate_hz,
            "acquisition_duration_s": self.acquisition_duration_s,
        }
        return _build_envelope(
            "asset.measurement",
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            source_event_id=self.source_event_id,
            batch_id=self.batch_id,
            timestamp=self.timestamp,
            source=self.source,
            asset_id=self.asset_id,
            asset_name=self.asset_name,
            plant=self.plant,
            area=self.area,
            data=data,
        )

    @classmethod
    def from_dict(cls, envelope: Dict[str, Any]) -> "AssetMeasurement":
        """Deserialize from an IAES wire-format dict."""
        asset = envelope.get("asset", {})
        data = envelope.get("data", {})
        return cls(
            asset_id=asset["asset_id"],
            measurement_type=data["measurement_type"],
            value=data["value"],
            unit=data["unit"],
            source=envelope.get("source", "sensors"),
            sensor_id=data.get("sensor_id"),
            location=data.get("location"),
            units_qualifier=data.get("units_qualifier"),
            sampling_rate_hz=data.get("sampling_rate_hz"),
            acquisition_duration_s=data.get("acquisition_duration_s"),
            asset_name=asset.get("asset_name"),
            plant=asset.get("plant"),
            area=asset.get("area"),
            event_id=envelope.get("event_id", _uuid4()),
            correlation_id=envelope.get("correlation_id", _uuid4()),
            source_event_id=envelope.get("source_event_id"),
            batch_id=envelope.get("batch_id"),
            timestamp=_parse_timestamp(envelope["timestamp"]),
        )


# ─── asset.health ───────────────────────────────────────────


@dataclass
class AssetHealth:
    """IAES ``asset.health`` — AI diagnosis or expert health assessment."""

    asset_id: str
    health_index: float = 1.0
    severity: Union[str, Severity] = Severity.INFO
    source: str = "diagnosis"

    # Fault classification
    anomaly_score: float = 0.0
    failure_mode: Optional[str] = None
    fault_confidence: float = 0.0
    rul_days: Optional[int] = None

    # Recommended action (folded into health per spec)
    recommended_action: Optional[str] = None
    estimated_downtime_hours: Optional[float] = None

    # ISO alignment (v1.2)
    iso_13374_status: Optional[Union[str, ISO13374Status]] = None
    iso_14224: Optional[Dict[str, Any]] = None

    # Asset identity
    asset_name: Optional[str] = None
    plant: Optional[str] = None
    area: Optional[str] = None

    # Envelope
    event_id: str = field(default_factory=_uuid4)
    correlation_id: str = field(default_factory=_uuid4)
    source_event_id: Optional[str] = None
    batch_id: Optional[str] = None
    timestamp: datetime = field(default_factory=_utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to an IAES wire-format dict."""
        data = {
            "health_index": self.health_index,
            "anomaly_score": self.anomaly_score,
            "severity": _enum_val(self.severity),
            "failure_mode": self.failure_mode,
            "fault_confidence": self.fault_confidence,
            "rul_days": self.rul_days,
            "recommended_action": self.recommended_action,
            "estimated_downtime_hours": self.estimated_downtime_hours,
            "iso_13374_status": _enum_val(self.iso_13374_status) if self.iso_13374_status else None,
            "iso_14224": self.iso_14224,
        }
        return _build_envelope(
            "asset.health",
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            source_event_id=self.source_event_id,
            batch_id=self.batch_id,
            timestamp=self.timestamp,
            source=self.source,
            asset_id=self.asset_id,
            asset_name=self.asset_name,
            plant=self.plant,
            area=self.area,
            data=data,
        )

    @classmethod
    def from_dict(cls, envelope: Dict[str, Any]) -> "AssetHealth":
        """Deserialize from an IAES wire-format dict."""
        asset = envelope.get("asset", {})
        data = envelope.get("data", {})
        return cls(
            asset_id=asset["asset_id"],
            health_index=data.get("health_index", 1.0),
            severity=data.get("severity", "info"),
            source=envelope.get("source", "diagnosis"),
            anomaly_score=data.get("anomaly_score", 0.0),
            failure_mode=data.get("failure_mode"),
            fault_confidence=data.get("fault_confidence", 0.0),
            rul_days=data.get("rul_days"),
            recommended_action=data.get("recommended_action"),
            estimated_downtime_hours=data.get("estimated_downtime_hours"),
            iso_13374_status=data.get("iso_13374_status"),
            iso_14224=data.get("iso_14224"),
            asset_name=asset.get("asset_name"),
            plant=asset.get("plant"),
            area=asset.get("area"),
            event_id=envelope.get("event_id", _uuid4()),
            correlation_id=envelope.get("correlation_id", _uuid4()),
            source_event_id=envelope.get("source_event_id"),
            batch_id=envelope.get("batch_id"),
            timestamp=_parse_timestamp(envelope["timestamp"]),
        )


# ─── maintenance.work_order_intent ──────────────────────────


@dataclass
class WorkOrderIntent:
    """IAES ``maintenance.work_order_intent`` — intent to create a work order."""

    asset_id: str
    title: str
    priority: Union[str, WorkOrderPriority] = WorkOrderPriority.MEDIUM
    source: str = "cmms"

    description: Optional[str] = None
    recommended_due_days: Optional[int] = None
    triggered_by: Optional[str] = None  # alert, schedule, manual, threshold, ai_diagnosis

    # Asset identity
    asset_name: Optional[str] = None
    plant: Optional[str] = None
    area: Optional[str] = None

    # Envelope
    event_id: str = field(default_factory=_uuid4)
    correlation_id: str = field(default_factory=_uuid4)
    source_event_id: Optional[str] = None
    batch_id: Optional[str] = None
    timestamp: datetime = field(default_factory=_utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to an IAES wire-format dict."""
        data = {
            "title": self.title,
            "description": self.description,
            "priority": _enum_val(self.priority),
            "recommended_due_days": self.recommended_due_days,
            "triggered_by": self.triggered_by,
        }
        return _build_envelope(
            "maintenance.work_order_intent",
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            source_event_id=self.source_event_id,
            batch_id=self.batch_id,
            timestamp=self.timestamp,
            source=self.source,
            asset_id=self.asset_id,
            asset_name=self.asset_name,
            plant=self.plant,
            area=self.area,
            data=data,
        )

    @classmethod
    def from_dict(cls, envelope: Dict[str, Any]) -> "WorkOrderIntent":
        """Deserialize from an IAES wire-format dict."""
        asset = envelope.get("asset", {})
        data = envelope.get("data", {})
        return cls(
            asset_id=asset["asset_id"],
            title=data["title"],
            priority=data.get("priority", "medium"),
            source=envelope.get("source", "cmms"),
            description=data.get("description"),
            recommended_due_days=data.get("recommended_due_days"),
            triggered_by=data.get("triggered_by"),
            asset_name=asset.get("asset_name"),
            plant=asset.get("plant"),
            area=asset.get("area"),
            event_id=envelope.get("event_id", _uuid4()),
            correlation_id=envelope.get("correlation_id", _uuid4()),
            source_event_id=envelope.get("source_event_id"),
            batch_id=envelope.get("batch_id"),
            timestamp=_parse_timestamp(envelope["timestamp"]),
        )


# ─── maintenance.completion ─────────────────────────────────


@dataclass
class MaintenanceCompletion:
    """IAES ``maintenance.completion`` — work order completion acknowledgment."""

    asset_id: str
    work_order_id: str
    status: Union[str, CompletionStatus] = CompletionStatus.COMPLETED
    source: str = "cmms"

    # Outcome details
    actual_duration_seconds: Optional[int] = None
    technician_id: Optional[str] = None
    checklist_completion_pct: Optional[float] = None
    completion_notes: Optional[str] = None
    spare_parts_count: Optional[int] = None
    failure_confirmed: Optional[bool] = None
    failure_mode: Optional[str] = None

    # ISO 14224 (v1.2)
    iso_14224: Optional[Dict[str, Any]] = None

    # Asset identity
    asset_name: Optional[str] = None
    plant: Optional[str] = None
    area: Optional[str] = None

    # Envelope
    event_id: str = field(default_factory=_uuid4)
    correlation_id: str = field(default_factory=_uuid4)
    source_event_id: Optional[str] = None
    batch_id: Optional[str] = None
    timestamp: datetime = field(default_factory=_utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to an IAES wire-format dict."""
        data = {
            "status": _enum_val(self.status),
            "work_order_id": self.work_order_id,
            "actual_duration_seconds": self.actual_duration_seconds,
            "technician_id": self.technician_id,
            "checklist_completion_pct": self.checklist_completion_pct,
            "completion_notes": self.completion_notes,
            "spare_parts_count": self.spare_parts_count,
            "failure_confirmed": self.failure_confirmed,
            "failure_mode": self.failure_mode,
            "iso_14224": self.iso_14224,
        }
        return _build_envelope(
            "maintenance.completion",
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            source_event_id=self.source_event_id,
            batch_id=self.batch_id,
            timestamp=self.timestamp,
            source=self.source,
            asset_id=self.asset_id,
            asset_name=self.asset_name,
            plant=self.plant,
            area=self.area,
            data=data,
        )

    @classmethod
    def from_dict(cls, envelope: Dict[str, Any]) -> "MaintenanceCompletion":
        """Deserialize from an IAES wire-format dict."""
        asset = envelope.get("asset", {})
        data = envelope.get("data", {})
        return cls(
            asset_id=asset["asset_id"],
            work_order_id=data["work_order_id"],
            status=data.get("status", "completed"),
            source=envelope.get("source", "cmms"),
            actual_duration_seconds=data.get("actual_duration_seconds"),
            technician_id=data.get("technician_id"),
            checklist_completion_pct=data.get("checklist_completion_pct"),
            completion_notes=data.get("completion_notes"),
            spare_parts_count=data.get("spare_parts_count"),
            failure_confirmed=data.get("failure_confirmed"),
            failure_mode=data.get("failure_mode"),
            iso_14224=data.get("iso_14224"),
            asset_name=asset.get("asset_name"),
            plant=asset.get("plant"),
            area=asset.get("area"),
            event_id=envelope.get("event_id", _uuid4()),
            correlation_id=envelope.get("correlation_id", _uuid4()),
            source_event_id=envelope.get("source_event_id"),
            batch_id=envelope.get("batch_id"),
            timestamp=_parse_timestamp(envelope["timestamp"]),
        )


# ─── asset.hierarchy ────────────────────────────────────────


@dataclass
class AssetHierarchy:
    """IAES ``asset.hierarchy`` — asset hierarchy structure sync."""

    asset_id: str
    hierarchy_level: Union[str, HierarchyLevel]
    relationship_type: Union[str, RelationshipType]
    source: str = "hierarchy"

    parent_asset_id: Optional[str] = None
    asset_type: Optional[str] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None

    # Asset identity
    asset_name: Optional[str] = None
    plant: Optional[str] = None
    area: Optional[str] = None

    # Envelope
    event_id: str = field(default_factory=_uuid4)
    correlation_id: str = field(default_factory=_uuid4)
    source_event_id: Optional[str] = None
    batch_id: Optional[str] = None
    timestamp: datetime = field(default_factory=_utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to an IAES wire-format dict."""
        data = {
            "hierarchy_level": _enum_val(self.hierarchy_level),
            "relationship_type": _enum_val(self.relationship_type),
            "parent_asset_id": self.parent_asset_id,
            "asset_type": self.asset_type,
            "serial_number": self.serial_number,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "location": self.location,
            "is_active": self.is_active,
        }
        return _build_envelope(
            "asset.hierarchy",
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            source_event_id=self.source_event_id,
            batch_id=self.batch_id,
            timestamp=self.timestamp,
            source=self.source,
            asset_id=self.asset_id,
            asset_name=self.asset_name,
            plant=self.plant,
            area=self.area,
            data=data,
        )

    @classmethod
    def from_dict(cls, envelope: Dict[str, Any]) -> "AssetHierarchy":
        """Deserialize from an IAES wire-format dict."""
        asset = envelope.get("asset", {})
        data = envelope.get("data", {})
        return cls(
            asset_id=asset["asset_id"],
            hierarchy_level=data["hierarchy_level"],
            relationship_type=data["relationship_type"],
            source=envelope.get("source", "hierarchy"),
            parent_asset_id=data.get("parent_asset_id"),
            asset_type=data.get("asset_type"),
            serial_number=data.get("serial_number"),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            location=data.get("location"),
            is_active=data.get("is_active"),
            asset_name=asset.get("asset_name"),
            plant=asset.get("plant"),
            area=asset.get("area"),
            event_id=envelope.get("event_id", _uuid4()),
            correlation_id=envelope.get("correlation_id", _uuid4()),
            source_event_id=envelope.get("source_event_id"),
            batch_id=envelope.get("batch_id"),
            timestamp=_parse_timestamp(envelope["timestamp"]),
        )


# ─── sensor.registration ───────────────────────────────────


@dataclass
class SensorRegistration:
    """IAES ``sensor.registration`` — sensor discovery and lifecycle."""

    asset_id: str
    sensor_id: str
    registration_status: Union[str, RegistrationStatus]
    source: str = "sensors"

    sensor_model: Optional[str] = None
    device_serial: Optional[str] = None
    firmware_version: Optional[str] = None
    measurement_capabilities: Optional[List[str]] = None
    calibration_date: Optional[str] = None
    communication_protocol: Optional[str] = None

    # Asset identity
    asset_name: Optional[str] = None
    plant: Optional[str] = None
    area: Optional[str] = None

    # Envelope
    event_id: str = field(default_factory=_uuid4)
    correlation_id: str = field(default_factory=_uuid4)
    source_event_id: Optional[str] = None
    batch_id: Optional[str] = None
    timestamp: datetime = field(default_factory=_utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to an IAES wire-format dict."""
        data = {
            "sensor_id": self.sensor_id,
            "registration_status": _enum_val(self.registration_status),
            "sensor_model": self.sensor_model,
            "device_serial": self.device_serial,
            "firmware_version": self.firmware_version,
            "measurement_capabilities": self.measurement_capabilities,
            "calibration_date": self.calibration_date,
            "communication_protocol": self.communication_protocol,
        }
        return _build_envelope(
            "sensor.registration",
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            source_event_id=self.source_event_id,
            batch_id=self.batch_id,
            timestamp=self.timestamp,
            source=self.source,
            asset_id=self.asset_id,
            asset_name=self.asset_name,
            plant=self.plant,
            area=self.area,
            data=data,
        )

    @classmethod
    def from_dict(cls, envelope: Dict[str, Any]) -> "SensorRegistration":
        """Deserialize from an IAES wire-format dict."""
        asset = envelope.get("asset", {})
        data = envelope.get("data", {})
        return cls(
            asset_id=asset["asset_id"],
            sensor_id=data["sensor_id"],
            registration_status=data["registration_status"],
            source=envelope.get("source", "sensors"),
            sensor_model=data.get("sensor_model"),
            device_serial=data.get("device_serial"),
            firmware_version=data.get("firmware_version"),
            measurement_capabilities=data.get("measurement_capabilities"),
            calibration_date=data.get("calibration_date"),
            communication_protocol=data.get("communication_protocol"),
            asset_name=asset.get("asset_name"),
            plant=asset.get("plant"),
            area=asset.get("area"),
            event_id=envelope.get("event_id", _uuid4()),
            correlation_id=envelope.get("correlation_id", _uuid4()),
            source_event_id=envelope.get("source_event_id"),
            batch_id=envelope.get("batch_id"),
            timestamp=_parse_timestamp(envelope["timestamp"]),
        )


# ─── maintenance.spare_part_usage ───────────────────────────


@dataclass
class SparePartUsage:
    """IAES ``maintenance.spare_part_usage`` — parts consumed during maintenance."""

    asset_id: str
    work_order_id: str
    spare_part_id: str
    quantity_used: float
    source: str = "cmms"

    part_number: Optional[str] = None
    part_name: Optional[str] = None
    unit_cost: Optional[float] = None
    currency: Optional[str] = None
    total_cost: Optional[float] = None

    # Asset identity
    asset_name: Optional[str] = None
    plant: Optional[str] = None
    area: Optional[str] = None

    # Envelope
    event_id: str = field(default_factory=_uuid4)
    correlation_id: str = field(default_factory=_uuid4)
    source_event_id: Optional[str] = None
    batch_id: Optional[str] = None
    timestamp: datetime = field(default_factory=_utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to an IAES wire-format dict."""
        data = {
            "work_order_id": self.work_order_id,
            "spare_part_id": self.spare_part_id,
            "quantity_used": self.quantity_used,
            "part_number": self.part_number,
            "part_name": self.part_name,
            "unit_cost": self.unit_cost,
            "currency": self.currency,
            "total_cost": self.total_cost,
        }
        return _build_envelope(
            "maintenance.spare_part_usage",
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            source_event_id=self.source_event_id,
            batch_id=self.batch_id,
            timestamp=self.timestamp,
            source=self.source,
            asset_id=self.asset_id,
            asset_name=self.asset_name,
            plant=self.plant,
            area=self.area,
            data=data,
        )

    @classmethod
    def from_dict(cls, envelope: Dict[str, Any]) -> "SparePartUsage":
        """Deserialize from an IAES wire-format dict."""
        asset = envelope.get("asset", {})
        data = envelope.get("data", {})
        return cls(
            asset_id=asset["asset_id"],
            work_order_id=data["work_order_id"],
            spare_part_id=data["spare_part_id"],
            quantity_used=data["quantity_used"],
            source=envelope.get("source", "cmms"),
            part_number=data.get("part_number"),
            part_name=data.get("part_name"),
            unit_cost=data.get("unit_cost"),
            currency=data.get("currency"),
            total_cost=data.get("total_cost"),
            asset_name=asset.get("asset_name"),
            plant=asset.get("plant"),
            area=asset.get("area"),
            event_id=envelope.get("event_id", _uuid4()),
            correlation_id=envelope.get("correlation_id", _uuid4()),
            source_event_id=envelope.get("source_event_id"),
            batch_id=envelope.get("batch_id"),
            timestamp=_parse_timestamp(envelope["timestamp"]),
        )


# ─── Lookup table for from_dict dispatch ────────────────────

EVENT_TYPES = {
    "asset.measurement": AssetMeasurement,
    "asset.health": AssetHealth,
    "maintenance.work_order_intent": WorkOrderIntent,
    "maintenance.completion": MaintenanceCompletion,
    "asset.hierarchy": AssetHierarchy,
    "sensor.registration": SensorRegistration,
    "maintenance.spare_part_usage": SparePartUsage,
}


def from_dict(envelope: Dict[str, Any]) -> Any:
    """Deserialize any IAES envelope dict to the corresponding model.

    Args:
        envelope: A dict with at least ``event_type`` and ``data`` keys.

    Returns:
        The appropriate IAES model instance.

    Raises:
        ValueError: If ``event_type`` is not recognized.
    """
    event_type = envelope.get("event_type")
    cls = EVENT_TYPES.get(event_type)  # type: ignore[arg-type]
    if cls is None:
        raise ValueError(f"Unknown IAES event_type: {event_type!r}")
    return cls.from_dict(envelope)
