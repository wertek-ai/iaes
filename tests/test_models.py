"""Tests for IAES event models — round-trip, serialization, from_dict."""

import json
from datetime import datetime, timezone

import iaes
from iaes import (
    AssetHealth,
    AssetHierarchy,
    AssetMeasurement,
    MaintenanceCompletion,
    SensorRegistration,
    SparePartUsage,
    WorkOrderIntent,
    Severity,
    MeasurementType,
    UnitsQualifier,
    ISO13374Status,
    WorkOrderPriority,
    CompletionStatus,
    HierarchyLevel,
    RelationshipType,
    RegistrationStatus,
    SPEC_VERSION,
    from_dict,
)


class TestAssetMeasurement:
    def test_basic_creation(self):
        e = AssetMeasurement(
            asset_id="MOTOR-001",
            measurement_type="vibration_velocity",
            value=4.2,
            unit="mm/s",
            source="acme.sensors",
        )
        d = e.to_dict()
        assert d["event_type"] == "asset.measurement"
        assert d["spec_version"] == SPEC_VERSION
        assert d["asset"]["asset_id"] == "MOTOR-001"
        assert d["data"]["measurement_type"] == "vibration_velocity"
        assert d["data"]["value"] == 4.2
        assert d["data"]["unit"] == "mm/s"
        assert len(d["content_hash"]) == 16

    def test_enum_measurement_type(self):
        e = AssetMeasurement(
            asset_id="P-001",
            measurement_type=MeasurementType.TEMPERATURE,
            value=85.3,
            unit="C",
        )
        d = e.to_dict()
        assert d["data"]["measurement_type"] == "temperature"

    def test_iso_17359_fields(self):
        e = AssetMeasurement(
            asset_id="M-001",
            measurement_type="vibration_velocity",
            value=4.2,
            unit="mm/s",
            units_qualifier=UnitsQualifier.RMS,
            sampling_rate_hz=25600.0,
            acquisition_duration_s=1.0,
        )
        d = e.to_dict()
        assert d["data"]["units_qualifier"] == "rms"
        assert d["data"]["sampling_rate_hz"] == 25600.0
        assert d["data"]["acquisition_duration_s"] == 1.0

    def test_none_fields_excluded(self):
        e = AssetMeasurement(
            asset_id="M-001",
            measurement_type="temperature",
            value=50.0,
            unit="C",
        )
        d = e.to_dict()
        assert "sensor_id" not in d["data"]
        assert "location" not in d["data"]
        assert "units_qualifier" not in d["data"]

    def test_round_trip(self):
        e = AssetMeasurement(
            asset_id="PUMP-002",
            measurement_type="pressure",
            value=3.5,
            unit="bar",
            sensor_id="SENS-42",
            location="inlet",
            source="scada.plc_01",
            asset_name="Pump P-002",
            plant="Plant A",
            area="Zone 3",
        )
        d = e.to_dict()
        e2 = AssetMeasurement.from_dict(d)
        assert e2.asset_id == "PUMP-002"
        assert e2.measurement_type == "pressure"
        assert e2.value == 3.5
        assert e2.sensor_id == "SENS-42"
        assert e2.source == "scada.plc_01"

    def test_json_serializable(self):
        e = AssetMeasurement(
            asset_id="M-001",
            measurement_type="vibration_velocity",
            value=4.2,
            unit="mm/s",
        )
        s = json.dumps(e.to_dict())
        assert isinstance(s, str)


class TestAssetHealth:
    def test_basic_creation(self):
        e = AssetHealth(
            asset_id="MOTOR-001",
            health_index=0.16,
            severity=Severity.CRITICAL,
            failure_mode="bearing_inner_race",
            rul_days=5,
            source="wertek.ai.vibration",
        )
        d = e.to_dict()
        assert d["event_type"] == "asset.health"
        assert d["data"]["health_index"] == 0.16
        assert d["data"]["severity"] == "critical"
        assert d["data"]["failure_mode"] == "bearing_inner_race"
        assert d["data"]["rul_days"] == 5

    def test_string_severity(self):
        e = AssetHealth(
            asset_id="M-001",
            severity="high",
        )
        d = e.to_dict()
        assert d["data"]["severity"] == "high"

    def test_iso_alignment(self):
        e = AssetHealth(
            asset_id="M-001",
            health_index=0.3,
            severity="high",
            iso_13374_status=ISO13374Status.UNACCEPTABLE,
            iso_14224={
                "mechanism_code": "1.1",
                "mechanism_label": "Mechanical wear",
                "cause_code": "1",
                "cause_label": "Design-related",
            },
        )
        d = e.to_dict()
        assert d["data"]["iso_13374_status"] == "unacceptable"
        assert d["data"]["iso_14224"]["mechanism_code"] == "1.1"

    def test_round_trip(self):
        e = AssetHealth(
            asset_id="M-001",
            health_index=0.5,
            severity="medium",
            failure_mode="misalignment",
            rul_days=30,
        )
        d = e.to_dict()
        e2 = AssetHealth.from_dict(d)
        assert e2.health_index == 0.5
        assert e2.failure_mode == "misalignment"
        assert e2.rul_days == 30


class TestWorkOrderIntent:
    def test_basic_creation(self):
        e = WorkOrderIntent(
            asset_id="MOTOR-001",
            title="Replace bearing DE",
            priority=WorkOrderPriority.HIGH,
            triggered_by="ai_diagnosis",
        )
        d = e.to_dict()
        assert d["event_type"] == "maintenance.work_order_intent"
        assert d["data"]["title"] == "Replace bearing DE"
        assert d["data"]["priority"] == "high"
        assert d["data"]["triggered_by"] == "ai_diagnosis"

    def test_round_trip(self):
        e = WorkOrderIntent(
            asset_id="P-003",
            title="Inspect pump seals",
            priority="medium",
            recommended_due_days=14,
        )
        d = e.to_dict()
        e2 = WorkOrderIntent.from_dict(d)
        assert e2.title == "Inspect pump seals"
        assert e2.recommended_due_days == 14


class TestMaintenanceCompletion:
    def test_basic_creation(self):
        e = MaintenanceCompletion(
            asset_id="M-001",
            work_order_id="WO-2026-001",
            status=CompletionStatus.COMPLETED,
            actual_duration_seconds=7200,
            failure_confirmed=True,
        )
        d = e.to_dict()
        assert d["event_type"] == "maintenance.completion"
        assert d["data"]["work_order_id"] == "WO-2026-001"
        assert d["data"]["actual_duration_seconds"] == 7200

    def test_round_trip(self):
        e = MaintenanceCompletion(
            asset_id="M-001",
            work_order_id="WO-123",
            completion_notes="Bearing replaced, alignment OK",
        )
        d = e.to_dict()
        e2 = MaintenanceCompletion.from_dict(d)
        assert e2.completion_notes == "Bearing replaced, alignment OK"


class TestAssetHierarchy:
    def test_basic_creation(self):
        e = AssetHierarchy(
            asset_id="PLANT-001",
            hierarchy_level=HierarchyLevel.PLANT,
            relationship_type=RelationshipType.CHILD_OF,
            parent_asset_id="ORG-001",
            asset_name="Pesqueria Plant",
        )
        d = e.to_dict()
        assert d["event_type"] == "asset.hierarchy"
        assert d["data"]["hierarchy_level"] == "plant"
        assert d["data"]["parent_asset_id"] == "ORG-001"

    def test_round_trip(self):
        e = AssetHierarchy(
            asset_id="EQ-001",
            hierarchy_level="equipment",
            relationship_type="child_of",
            manufacturer="SKF",
            model="6205-2RS",
        )
        d = e.to_dict()
        e2 = AssetHierarchy.from_dict(d)
        assert e2.manufacturer == "SKF"


class TestSensorRegistration:
    def test_basic_creation(self):
        e = SensorRegistration(
            asset_id="M-001",
            sensor_id="CT-MCSA-001",
            registration_status=RegistrationStatus.REGISTERED,
            sensor_model="SCT-013-030",
            communication_protocol="mqtt",
        )
        d = e.to_dict()
        assert d["event_type"] == "sensor.registration"
        assert d["data"]["sensor_id"] == "CT-MCSA-001"

    def test_round_trip(self):
        e = SensorRegistration(
            asset_id="M-001",
            sensor_id="S-001",
            registration_status="discovered",
            measurement_capabilities=["vibration_velocity", "temperature"],
        )
        d = e.to_dict()
        e2 = SensorRegistration.from_dict(d)
        assert e2.measurement_capabilities == ["vibration_velocity", "temperature"]


class TestSparePartUsage:
    def test_basic_creation(self):
        e = SparePartUsage(
            asset_id="M-001",
            work_order_id="WO-001",
            spare_part_id="SP-6205",
            quantity_used=2,
            unit_cost=45.00,
            currency="USD",
        )
        d = e.to_dict()
        assert d["event_type"] == "maintenance.spare_part_usage"
        assert d["data"]["quantity_used"] == 2
        assert d["data"]["unit_cost"] == 45.00

    def test_round_trip(self):
        e = SparePartUsage(
            asset_id="M-001",
            work_order_id="WO-001",
            spare_part_id="SP-001",
            quantity_used=1.5,
            part_name="Bearing SKF 6205",
        )
        d = e.to_dict()
        e2 = SparePartUsage.from_dict(d)
        assert e2.part_name == "Bearing SKF 6205"
        assert e2.quantity_used == 1.5


class TestFromDict:
    def test_dispatch_measurement(self):
        wire = AssetMeasurement(
            asset_id="M-001",
            measurement_type="temperature",
            value=80.0,
            unit="C",
        ).to_dict()
        obj = from_dict(wire)
        assert isinstance(obj, AssetMeasurement)
        assert obj.value == 80.0

    def test_dispatch_health(self):
        wire = AssetHealth(asset_id="M-001", severity="high").to_dict()
        obj = from_dict(wire)
        assert isinstance(obj, AssetHealth)

    def test_unknown_event_type(self):
        try:
            from_dict({"event_type": "foo.bar", "data": {}})
            assert False, "Should have raised"
        except ValueError as e:
            assert "foo.bar" in str(e)


class TestBatchId:
    def test_batch_id_included(self):
        e = AssetMeasurement(
            asset_id="M-001",
            measurement_type="temperature",
            value=50.0,
            unit="C",
            batch_id="BATCH-001",
        )
        d = e.to_dict()
        assert d["batch_id"] == "BATCH-001"

    def test_batch_id_excluded_when_none(self):
        e = AssetMeasurement(
            asset_id="M-001",
            measurement_type="temperature",
            value=50.0,
            unit="C",
        )
        d = e.to_dict()
        assert "batch_id" not in d


class TestSourceEventId:
    def test_source_event_id_included(self):
        e = AssetHealth(
            asset_id="M-001",
            source_event_id="abc-123",
        )
        d = e.to_dict()
        assert d["source_event_id"] == "abc-123"

    def test_source_event_id_excluded_when_none(self):
        e = AssetHealth(asset_id="M-001")
        d = e.to_dict()
        assert "source_event_id" not in d


class TestContentHash:
    def test_deterministic(self):
        e1 = AssetMeasurement(
            asset_id="M-001",
            measurement_type="temperature",
            value=50.0,
            unit="C",
        )
        e2 = AssetMeasurement(
            asset_id="M-001",
            measurement_type="temperature",
            value=50.0,
            unit="C",
        )
        assert e1.to_dict()["content_hash"] == e2.to_dict()["content_hash"]

    def test_different_data_different_hash(self):
        e1 = AssetMeasurement(
            asset_id="M-001",
            measurement_type="temperature",
            value=50.0,
            unit="C",
        )
        e2 = AssetMeasurement(
            asset_id="M-001",
            measurement_type="temperature",
            value=51.0,
            unit="C",
        )
        assert e1.to_dict()["content_hash"] != e2.to_dict()["content_hash"]


class TestVersion:
    def test_spec_version(self):
        assert SPEC_VERSION == "1.2"

    def test_package_version(self):
        assert iaes.__version__ == "0.1.0"
