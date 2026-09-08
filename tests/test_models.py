"""Tests for IAES event models — round-trip, serialization, from_object."""

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
    ConditionTrend,
    WorkOrderPriority,
    CompletionStatus,
    HierarchyLevel,
    RelationshipType,
    RegistrationStatus,
    SPEC_VERSION,
    from_object,
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
        e2 = AssetMeasurement.from_object(d)
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
            source="acme.vibration",
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

    def test_condition_trend(self):
        e = AssetHealth(
            asset_id="M-001",
            health_index=0.4,
            severity="high",
            condition_trend=ConditionTrend.WORSENING,
        )
        d = e.to_dict()
        assert d["data"]["condition_trend"] == "worsening"
        e2 = AssetHealth.from_object(d)
        assert e2.condition_trend == "worsening"

    def test_condition_trend_string(self):
        e = AssetHealth(
            asset_id="M-001",
            condition_trend="improving",
        )
        d = e.to_dict()
        assert d["data"]["condition_trend"] == "improving"

    def test_condition_trend_optional(self):
        e = AssetHealth(asset_id="M-001")
        d = e.to_dict()
        assert "condition_trend" not in d["data"]

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
        e2 = AssetHealth.from_object(d)
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
        e2 = WorkOrderIntent.from_object(d)
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
        e2 = MaintenanceCompletion.from_object(d)
        assert e2.completion_notes == "Bearing replaced, alignment OK"


class TestAssetHierarchy:
    def test_basic_creation(self):
        e = AssetHierarchy(
            asset_id="PLANT-001",
            hierarchy_level=HierarchyLevel.PLANT,
            relationship_type=RelationshipType.CHILD_OF,
            parent_asset_id="ORG-001",
            asset_name="Planta Norte Plant",
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
        e2 = AssetHierarchy.from_object(d)
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
        e2 = SensorRegistration.from_object(d)
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
        e2 = SparePartUsage.from_object(d)
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
        obj = from_object(wire)
        assert isinstance(obj, AssetMeasurement)
        assert obj.value == 80.0

    def test_dispatch_health(self):
        wire = AssetHealth(asset_id="M-001", severity="high").to_dict()
        obj = from_object(wire)
        assert isinstance(obj, AssetHealth)

    def test_unknown_event_type(self):
        try:
            from_object({"event_type": "foo.bar", "data": {}})
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


class TestPublishedReadmesDeclareTheFamily:
    """GOVERNANCE.md §3.2 — every package page states the family and the spec.

    The rule is normative because it rots otherwise, and it had: the SDK's npm
    page advertised **IAES v1.2**, two versions behind, while two other pages
    said v1.3. A version claim is the first thing an integrator reads and the
    last thing anybody remembers to update.

    ⚠️ Note what this deliberately does NOT check: the mere presence of an old
    version string. The root README cites the Zenodo deposit, which really is
    v1.3 until v1.4 is deposited — a naive rule would force falsifying a
    citation. What is checked is that the CURRENT spec is declared, not that
    older ones are absent.
    """

    READMES = ["README.md", "npm/README.md", "node-red/README.md", "n8n-nodes/README.md"]
    PACKAGES = ["@iaes/sdk", "pip install iaes", "node-red-contrib-iaes", "n8n-nodes-iaes"]

    def _read(self, rel):
        """Read a README with whitespace normalised.

        A guard that depends on where a line happens to wrap breaks the first
        time somebody reformats the file — the same failure as anchoring to a
        byte window. It should assert about the prose, not the layout.
        """
        import pathlib
        import re
        root = pathlib.Path(__file__).resolve().parents[1]
        return re.sub(r"\s+", " ", (root / rel).read_text(encoding="utf-8"))

    def test_each_page_lists_all_four_packages(self):
        for rel in self.READMES:
            text = self._read(rel)
            for pkg in self.PACKAGES:
                assert pkg in text, (
                    f"{rel} does not mention {pkg!r} — somebody landing there "
                    "has no way to learn the other runtimes exist"
                )

    def test_each_page_declares_the_current_spec_version(self):
        for rel in self.READMES:
            text = self._read(rel)
            assert f"IAES {SPEC_VERSION}" in text or f"IAES v{SPEC_VERSION}" in text, (
                f"{rel} never states which specification it implements "
                f"(expected {SPEC_VERSION})"
            )

    def test_each_page_explains_that_the_version_carries_the_spec(self):
        for rel in self.READMES:
            assert "first two numbers" in self._read(rel), (
                f"{rel} does not explain the version scheme (GOVERNANCE.md §3.1)"
            )


class TestBundledSchemasMatchTheCanonicalOnes:
    """The schemas live in four copies and two of them are PUBLISHED.

    `npm/schemas/` ships inside @iaes/sdk and `src/iaes/schemas/` ships inside
    the PyPI wheel — and the Python validator reads its copy at runtime. When
    the $id was corrected in v1.4, two surfaces were synced and these two were
    not: they kept pointing at a host that never resolved, and tagging would
    have installed the defect on every user.

    Four copies nobody watches drift again. This is the watch.
    """

    def _paths(self):
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[1]
        return root / "schema", [root / "npm" / "schemas", root / "src" / "iaes" / "schemas"]

    def test_every_bundled_copy_is_byte_identical(self):
        canonical, bundled = self._paths()
        originals = sorted(canonical.glob("*.schema.json"))
        assert len(originals) == 8, "expected 8 canonical schemas"

        for copy_dir in bundled:
            for original in originals:
                mirror = copy_dir / original.name
                assert mirror.exists(), f"{mirror} is missing — it ships to users"
                assert mirror.read_bytes() == original.read_bytes(), (
                    f"{mirror} differs from the canonical schema. This copy is "
                    "published; a stale one installs the wrong contract."
                )

    def test_the_validator_reads_a_current_copy(self):
        """The runtime copy must carry what v1.4 added, or the SDK validates
        against a contract the specification no longer describes."""
        import json
        _, bundled = self._paths()
        envelope = json.loads((bundled[1] / "iaes-envelope.schema.json").read_text(encoding="utf-8"))
        assert envelope["$id"].startswith("https://iaes.dev/"), "stale $id in the shipped copy"
        assert "dataschema" in envelope["properties"]
        assert "enum" not in envelope["properties"]["event_type"]


class TestEventTypeIsOpen:
    """v1.4 — event_type was a closed enumeration while the specification
    ordered consumers to tolerate values they do not recognise. Nobody could
    produce one. It is now a shape."""

    PATTERN = r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_.]*$"

    def _envelope_schema(self):
        import json
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[1]
        return json.loads((root / "schema" / "iaes-envelope.schema.json").read_text(encoding="utf-8"))

    def test_the_enumeration_is_gone(self):
        et = self._envelope_schema()["properties"]["event_type"]
        assert "enum" not in et, "a closed enum makes an unknown type impossible to produce"
        assert et["pattern"] == self.PATTERN
        assert len(et["examples"]) == 7, "the published types survive as examples"

    def test_every_published_type_still_validates(self):
        """Widening only counts if nothing that used to pass now fails."""
        import re
        et = self._envelope_schema()["properties"]["event_type"]
        for t in et["examples"]:
            assert re.match(et["pattern"], t), t

    def test_a_producer_can_define_its_own(self):
        import re
        for t in ("acme.press_stroke", "vendor.line_state", "plant_a.batch_end"):
            assert re.match(self.PATTERN, t), t

    def test_it_still_has_to_look_like_an_event_type(self):
        """Open is not shapeless: a namespace is still required."""
        import re
        for bad in ("NotAType", "measurement", "Asset.Measurement", ".leading", "1.numeric"):
            assert not re.match(self.PATTERN, bad), bad


class TestDataschema:
    """v1.4 — every message carries the URI of its own contract."""

    def test_published_event_type_gets_its_schema_uri(self):
        e = AssetMeasurement(
            asset_id="MOTOR-001",
            measurement_type="vibration_velocity",
            value=4.2,
            unit="mm/s",
        ).to_dict()
        assert e["dataschema"] == "https://iaes.dev/schema/v1/asset.measurement"

    def test_the_uri_is_the_event_type(self):
        """The slug of every published schema is its event_type, which is why
        the field can be derived instead of asked for."""
        from iaes.envelope import SCHEMA_BASE, schema_uri_for

        for event_type in ("asset.health", "sensor.registration",
                           "maintenance.work_order_intent"):
            assert schema_uri_for(event_type) == SCHEMA_BASE + event_type

    def test_an_unpublished_event_type_gets_nothing(self):
        """A URI that does not resolve is worse than an absent field — that was
        the defect v1.4 corrected in the schemas themselves."""
        from iaes.envelope import schema_uri_for

        assert schema_uri_for("vendor.custom_event") is None


class TestVersion:
    def test_spec_version(self):
        assert SPEC_VERSION == "1.4"

    def test_package_version(self):
        assert iaes.__version__ == "1.4.1"

    def test_the_package_version_declares_the_spec_it_implements(self):
        """GOVERNANCE.md §3.1 — the first two numbers ARE the specification.

        A reader should be able to tell what a package is compatible with by
        looking at its version, without opening anything. That only holds if
        something enforces it, so this is the something.
        """
        major_minor = ".".join(iaes.__version__.split(".")[:2])
        assert major_minor == SPEC_VERSION, (
            "package version %s claims spec %s but the SDK implements %s"
            % (iaes.__version__, major_minor, SPEC_VERSION)
        )

    def test_reported_version_matches_the_published_one(self):
        """__version__ and pyproject must agree.

        They did not: pyproject and PyPI said 0.3.0 while the package reported
        0.2.1 at runtime, and the pinned test above protected the drift instead
        of catching it. A literal in two files always drifts; this makes the
        drift fail the build.
        """
        import pathlib
        import re

        pyproject = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
        text = pyproject.read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
        assert match, "no version in pyproject.toml"
        assert iaes.__version__ == match.group(1), (
            "iaes.__version__ is %s but pyproject.toml publishes %s"
            % (iaes.__version__, match.group(1))
        )
