"""Cross-language roundtrip test: Python generates -> TS validates, and vice versa.

This test:
1. Python generates 7 events -> writes JSON fixtures
2. Calls Node.js to validate those fixtures with the TS SDK
3. Node.js generates 7 events -> writes JSON fixtures
4. Python validates those fixtures against JSON schemas
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from iaes import (
    AssetHealth,
    AssetHierarchy,
    AssetMeasurement,
    MaintenanceCompletion,
    SensorRegistration,
    SparePartUsage,
    WorkOrderIntent,
    from_dict,
    validate,
)

NPM_DIR = Path(__file__).parent.parent / "npm"


def _python_fixtures() -> dict:
    """Generate one event per type from Python SDK."""
    return {
        "measurement": AssetMeasurement(
            asset_id="CROSS-001",
            measurement_type="vibration_velocity",
            value=4.2,
            unit="mm/s",
            source="python.test",
            units_qualifier="rms",
            sampling_rate_hz=25600.0,
            event_id="py-meas-001",
            correlation_id="py-corr-001",
            timestamp="2026-03-08T12:00:00+00:00",
        ).to_dict(),
        "health": AssetHealth(
            asset_id="CROSS-001",
            health_index=0.16,
            severity="critical",
            failure_mode="bearing_inner_race",
            rul_days=5,
            source="python.test",
            iso_13374_status="unacceptable",
            event_id="py-health-001",
            correlation_id="py-corr-002",
            timestamp="2026-03-08T12:01:00+00:00",
        ).to_dict(),
        "work_order": WorkOrderIntent(
            asset_id="CROSS-001",
            title="Replace bearing DE",
            priority="high",
            triggered_by="ai_diagnosis",
            source="python.test",
            event_id="py-wo-001",
            correlation_id="py-corr-003",
            timestamp="2026-03-08T12:02:00+00:00",
        ).to_dict(),
        "completion": MaintenanceCompletion(
            asset_id="CROSS-001",
            work_order_id="WO-001",
            actual_duration_seconds=7200,
            source="python.test",
            event_id="py-comp-001",
            correlation_id="py-corr-004",
            timestamp="2026-03-08T12:03:00+00:00",
        ).to_dict(),
        "hierarchy": AssetHierarchy(
            asset_id="CROSS-001",
            hierarchy_level="equipment",
            relationship_type="child_of",
            manufacturer="SKF",
            source="python.test",
            event_id="py-hier-001",
            correlation_id="py-corr-005",
            timestamp="2026-03-08T12:04:00+00:00",
        ).to_dict(),
        "sensor": SensorRegistration(
            asset_id="CROSS-001",
            sensor_id="CT-001",
            registration_status="registered",
            communication_protocol="mqtt",
            source="python.test",
            event_id="py-sens-001",
            correlation_id="py-corr-006",
            timestamp="2026-03-08T12:05:00+00:00",
        ).to_dict(),
        "spare_part": SparePartUsage(
            asset_id="CROSS-001",
            work_order_id="WO-001",
            spare_part_id="SP-6205",
            quantity_used=2,
            unit_cost=45.0,
            currency="USD",
            source="python.test",
            event_id="py-spare-001",
            correlation_id="py-corr-007",
            timestamp="2026-03-08T12:06:00+00:00",
        ).to_dict(),
    }


# JavaScript that validates Python fixtures and generates TS fixtures
_NPM_DIST = str((Path(__file__).parent.parent / "npm" / "dist").as_posix())

_TS_VALIDATOR_SCRIPT_TEMPLATE = """
const fs = require('fs');
const path = require('path');
const {
  AssetMeasurement, AssetHealth, WorkOrderIntent,
  MaintenanceCompletion, AssetHierarchy, SensorRegistration,
  SparePartUsage, fromJSON
} = require('__NPM_DIST__/index');

// Step 1: Read Python fixtures and validate by deserializing
const pyFixtures = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const errors = [];

for (const [name, envelope] of Object.entries(pyFixtures)) {
  try {
    const obj = fromJSON(envelope);
    if (obj.asset_id !== 'CROSS-001') {
      errors.push(name + ': wrong asset_id ' + obj.asset_id);
    }
  } catch (e) {
    errors.push(name + ': ' + e.message);
  }
}

if (errors.length > 0) {
  console.error('Python -> TS validation failed:', errors);
  process.exit(1);
}

// Step 2: Generate TS fixtures for Python to validate
const tsFixtures = {
  measurement: new AssetMeasurement({
    asset_id: 'CROSS-002',
    measurement_type: 'temperature',
    value: 85.3,
    unit: 'C',
    source: 'ts.test',
    event_id: 'ts-meas-001',
    correlation_id: 'ts-corr-001',
    timestamp: '2026-03-08T13:00:00.000Z',
  }).toJSON(),
  health: new AssetHealth({
    asset_id: 'CROSS-002',
    health_index: 0.72,
    severity: 'medium',
    failure_mode: 'misalignment',
    source: 'ts.test',
    event_id: 'ts-health-001',
    correlation_id: 'ts-corr-002',
    timestamp: '2026-03-08T13:01:00.000Z',
  }).toJSON(),
  work_order: new WorkOrderIntent({
    asset_id: 'CROSS-002',
    title: 'Align motor',
    priority: 'medium',
    source: 'ts.test',
    event_id: 'ts-wo-001',
    correlation_id: 'ts-corr-003',
    timestamp: '2026-03-08T13:02:00.000Z',
  }).toJSON(),
  completion: new MaintenanceCompletion({
    asset_id: 'CROSS-002',
    work_order_id: 'WO-TS-001',
    source: 'ts.test',
    event_id: 'ts-comp-001',
    correlation_id: 'ts-corr-004',
    timestamp: '2026-03-08T13:03:00.000Z',
  }).toJSON(),
  hierarchy: new AssetHierarchy({
    asset_id: 'CROSS-002',
    hierarchy_level: 'plant',
    relationship_type: 'child_of',
    source: 'ts.test',
    event_id: 'ts-hier-001',
    correlation_id: 'ts-corr-005',
    timestamp: '2026-03-08T13:04:00.000Z',
  }).toJSON(),
  sensor: new SensorRegistration({
    asset_id: 'CROSS-002',
    sensor_id: 'S-TS-001',
    registration_status: 'discovered',
    source: 'ts.test',
    event_id: 'ts-sens-001',
    correlation_id: 'ts-corr-006',
    timestamp: '2026-03-08T13:05:00.000Z',
  }).toJSON(),
  spare_part: new SparePartUsage({
    asset_id: 'CROSS-002',
    work_order_id: 'WO-TS-001',
    spare_part_id: 'SP-TS-001',
    quantity_used: 1,
    source: 'ts.test',
    event_id: 'ts-spare-001',
    correlation_id: 'ts-corr-007',
    timestamp: '2026-03-08T13:06:00.000Z',
  }).toJSON(),
};

fs.writeFileSync(process.argv[3], JSON.stringify(tsFixtures, null, 2));
console.log('OK: Python fixtures validated, TS fixtures generated');
"""


class TestCrossLanguageRoundtrip:
    """Python <-> TypeScript cross-validation."""

    def test_roundtrip(self, tmp_path):
        # Write Python fixtures
        py_fixtures = _python_fixtures()
        py_path = tmp_path / "py_fixtures.json"
        ts_path = tmp_path / "ts_fixtures.json"
        script_path = tmp_path / "validate.js"

        py_path.write_text(json.dumps(py_fixtures, indent=2), encoding="utf-8")
        script = _TS_VALIDATOR_SCRIPT_TEMPLATE.replace("__NPM_DIST__", _NPM_DIST)
        script_path.write_text(script, encoding="utf-8")

        # Run Node.js: validate Python fixtures + generate TS fixtures
        repo_root = Path(__file__).parent.parent
        result = subprocess.run(
            ["node", str(script_path), str(py_path), str(ts_path)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Node.js validation failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Read TS-generated fixtures
        ts_fixtures = json.loads(ts_path.read_text())

        # Validate each TS fixture with Python SDK
        for name, envelope in ts_fixtures.items():
            # Schema validation
            validate(envelope)

            # Model deserialization
            obj = from_dict(envelope)
            assert obj.asset_id == "CROSS-002", f"{name}: wrong asset_id"
            assert obj.source == "ts.test", f"{name}: wrong source"

    def test_content_hash_cross_language(self, tmp_path):
        """Verify content_hash is identical between Python and TS for same data."""
        py_fixtures = _python_fixtures()

        # The Python content_hash for measurement
        py_hash = py_fixtures["measurement"]["content_hash"]

        # Generate same event in TS and compare hash
        script = f"""
const path = require('path');
const {{ AssetMeasurement }} = require(path.join('{str(Path(__file__).parent.parent / "npm" / "dist").replace(chr(92), "/")}', 'index'));
const event = new AssetMeasurement({{
  asset_id: 'CROSS-001',
  measurement_type: 'vibration_velocity',
  value: 4.2,
  unit: 'mm/s',
  source: 'python.test',
  units_qualifier: 'rms',
  sampling_rate_hz: 25600,
}});
console.log(event.toJSON().content_hash);
"""
        script_path = tmp_path / "hash_test.js"
        script_path.write_text(script, encoding="utf-8")
        result = subprocess.run(
            ["node", str(script_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        ts_hash = result.stdout.strip()
        assert py_hash == ts_hash, f"Hash mismatch: Python={py_hash} TS={ts_hash}"
