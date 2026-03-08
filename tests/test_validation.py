"""Tests for IAES schema validation."""

import pytest

from iaes import (
    AssetHealth,
    AssetMeasurement,
    MaintenanceCompletion,
    WorkOrderIntent,
    AssetHierarchy,
    SensorRegistration,
    SparePartUsage,
    validate,
    load_schema,
    ValidationError,
)


class TestLoadSchema:
    def test_load_measurement_schema(self):
        schema = load_schema("asset.measurement")
        assert schema["title"] == "IAES asset.measurement"

    def test_load_health_schema(self):
        schema = load_schema("asset.health")
        assert "health_index" in str(schema)

    def test_load_unknown_raises(self):
        with pytest.raises(ValueError, match="No schema"):
            load_schema("unknown.type")


class TestValidate:
    def test_valid_measurement(self):
        event = AssetMeasurement(
            asset_id="M-001",
            measurement_type="vibration_velocity",
            value=4.2,
            unit="mm/s",
            source="acme.sensors",
        )
        validate(event.to_dict())  # should not raise

    def test_valid_health(self):
        event = AssetHealth(
            asset_id="M-001",
            health_index=0.8,
            severity="medium",
            source="acme.diagnosis",
        )
        validate(event.to_dict())

    def test_valid_work_order_intent(self):
        event = WorkOrderIntent(
            asset_id="M-001",
            title="Inspect bearing",
            priority="high",
            source="acme.cmms",
        )
        validate(event.to_dict())

    def test_valid_completion(self):
        event = MaintenanceCompletion(
            asset_id="M-001",
            work_order_id="WO-001",
            source="acme.cmms",
        )
        validate(event.to_dict())

    def test_valid_hierarchy(self):
        event = AssetHierarchy(
            asset_id="PLANT-001",
            hierarchy_level="plant",
            relationship_type="child_of",
            source="acme.hierarchy",
        )
        validate(event.to_dict())

    def test_valid_sensor_registration(self):
        event = SensorRegistration(
            asset_id="M-001",
            sensor_id="S-001",
            registration_status="discovered",
            source="acme.sensors",
        )
        validate(event.to_dict())

    def test_valid_spare_part_usage(self):
        event = SparePartUsage(
            asset_id="M-001",
            work_order_id="WO-001",
            spare_part_id="SP-001",
            quantity_used=2,
            source="acme.cmms",
        )
        validate(event.to_dict())

    def test_missing_event_type(self):
        with pytest.raises(ValidationError, match="Missing"):
            validate({"data": {}})

    def test_invalid_event_fails(self):
        bad = {
            "spec_version": "1.2",
            "event_type": "asset.measurement",
            "event_id": "abc",
            "correlation_id": "def",
            "timestamp": "2026-01-01T00:00:00Z",
            "source": "test",
            "content_hash": "0" * 16,
            "asset": {"asset_id": "M-001"},
            "data": {},  # missing required fields
        }
        with pytest.raises(ValidationError):
            validate(bad)


class TestValidateExamples:
    """Validate bundled JSON examples against schemas."""

    def _load_example(self, name):
        import json
        from pathlib import Path

        example_path = Path(__file__).parent.parent / "examples" / name
        with open(example_path) as f:
            return json.load(f)

    def test_asset_measurement_example(self):
        data = self._load_example("asset-measurement.json")
        validate(data)

    def test_asset_health_ai_example(self):
        data = self._load_example("asset-health-ai.json")
        validate(data)

    def test_asset_health_human_example(self):
        data = self._load_example("asset-health-human.json")
        validate(data)

    def test_work_order_intent_example(self):
        data = self._load_example("work-order-intent.json")
        validate(data)

    def test_maintenance_completion_example(self):
        data = self._load_example("maintenance-completion.json")
        validate(data)

    def test_asset_hierarchy_example(self):
        data = self._load_example("asset-hierarchy.json")
        # hierarchy example may be an array of events
        if isinstance(data, list):
            for event in data:
                validate(event)
        else:
            validate(data)

    def test_sensor_registration_example(self):
        data = self._load_example("sensor-registration.json")
        validate(data)

    def test_spare_part_usage_example(self):
        data = self._load_example("spare-part-usage.json")
        validate(data)
