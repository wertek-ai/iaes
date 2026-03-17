"""
IAES Example: Vibration Monitoring Simulation
==============================================

Simulates a pump with increasing vibration that triggers:
  1. Normal measurements
  2. Warning health alert (vibration exceeds 7.1 mm/s)
  3. Critical health alert with diagnosis
  4. Automatic work order intent
  5. Recovery after maintenance

Run:
    pip install iaes
    python vibration_monitor.py
"""

import json
import random
from iaes import (
    AssetMeasurement,
    AssetHealth,
    WorkOrderIntent,
    Severity,
    ConditionTrend,
)

# -- Setup ---------------------------------------------------------
ASSET = "PUMP-101"
PLANT = "Monterrey-North"
AREA = "Cooling Tower #3"
CORRELATION = f"{ASSET}:bearing_outer_race"
published = []

# ISO 17359 vibration alarm zones (mm/s RMS, Zone A-D)
ZONE_B = 4.5   # satisfactory
ZONE_C = 7.1   # unsatisfactory -> warning
ZONE_D = 11.2  # unacceptable -> critical


def publish(event, pretty=True):
    """Print IAES event JSON to stdout (swap with Client for real endpoint)."""
    payload = event.to_dict()
    published.append(payload)
    indent = 2 if pretty else None
    print(json.dumps(payload, indent=indent, default=str))


print("=" * 60)
print("  IAES Vibration Monitor -- Pump Bearing Degradation Demo")
print("=" * 60)
print()

# -- Phase 1: Normal readings ------------------------------------
print("> Phase 1: Normal operation (3 readings)")
print("-" * 40)
for i in range(3):
    vibration = round(random.uniform(2.0, 4.0), 1)
    event = AssetMeasurement(
        asset_id=ASSET,
        asset_name="Cooling Water Pump",
        plant=PLANT,
        area=AREA,
        measurement_type="vibration_rms",
        value=vibration,
        unit="mm/s",
        units_qualifier="rms",
        sampling_rate_hz=25600,
        source="sensor.accelerometer.sku200",
    )
    publish(event)
    print()

# -- Phase 2: Vibration increasing -> Warning --------------------
print("> Phase 2: Vibration increasing -- WARNING threshold")
print("-" * 40)
vibration = round(random.uniform(7.5, 9.0), 1)
measurement = AssetMeasurement(
    asset_id=ASSET,
    asset_name="Cooling Water Pump",
    plant=PLANT,
    area=AREA,
    measurement_type="vibration_rms",
    value=vibration,
    unit="mm/s",
    units_qualifier="rms",
    sampling_rate_hz=25600,
    correlation_id=CORRELATION,
    source="sensor.accelerometer.sku200",
)
publish(measurement)
print()

# Health alert -- onset
alert = AssetHealth(
    asset_id=ASSET,
    asset_name="Cooling Water Pump",
    plant=PLANT,
    area=AREA,
    health_index=0.55,
    severity=Severity.HIGH,
    failure_mode="bearing_outer_race",
    condition_trend=ConditionTrend.WORSENING,
    iso_13374_status="unsatisfactory",
    rul_days=14,
    recommended_action="Schedule bearing inspection within 2 weeks",
    correlation_id=CORRELATION,
    source="wertek.ai.vibration_classifier",
)
publish(alert)
print()

# -- Phase 3: Critical -> Work Order -----------------------------
print("> Phase 3: Critical vibration -- WORK ORDER generated")
print("-" * 40)
vibration = round(random.uniform(12.0, 15.0), 1)
measurement_crit = AssetMeasurement(
    asset_id=ASSET,
    asset_name="Cooling Water Pump",
    plant=PLANT,
    area=AREA,
    measurement_type="vibration_rms",
    value=vibration,
    unit="mm/s",
    units_qualifier="rms",
    correlation_id=CORRELATION,
    source="sensor.accelerometer.sku200",
)
publish(measurement_crit)
print()

critical = AssetHealth(
    asset_id=ASSET,
    health_index=0.16,
    severity=Severity.CRITICAL,
    failure_mode="bearing_outer_race",
    condition_trend=ConditionTrend.WORSENING,
    iso_13374_status="unacceptable",
    rul_days=3,
    recommended_action="Replace bearing immediately -- risk of seizure",
    correlation_id=CORRELATION,
    source="wertek.ai.vibration_classifier",
)
publish(critical)
print()

wo = WorkOrderIntent(
    asset_id=ASSET,
    asset_name="Cooling Water Pump",
    plant=PLANT,
    area=AREA,
    title="Replace outer race bearing -- PUMP-101",
    priority="critical",
    description="Vibration RMS exceeded Zone D (11.2 mm/s). AI diagnosis: bearing outer race defect. RUL: 3 days.",
    correlation_id=CORRELATION,
    source="wertek.ai.auto_wo",
)
publish(wo)
print()

# -- Phase 4: Recovery -------------------------------------------
print("> Phase 4: After maintenance -- RECOVERY")
print("-" * 40)
vibration = round(random.uniform(1.5, 3.0), 1)
recovery_measurement = AssetMeasurement(
    asset_id=ASSET,
    asset_name="Cooling Water Pump",
    plant=PLANT,
    area=AREA,
    measurement_type="vibration_rms",
    value=vibration,
    unit="mm/s",
    units_qualifier="rms",
    correlation_id=CORRELATION,
    source="sensor.accelerometer.sku200",
)
publish(recovery_measurement)
print()

recovery = AssetHealth(
    asset_id=ASSET,
    health_index=0.92,
    severity=Severity.INFO,
    failure_mode="bearing_outer_race",
    condition_trend=ConditionTrend.IMPROVING,
    iso_13374_status="normal",
    recommended_action="Bearing replaced. Asset returned to normal operation.",
    correlation_id=CORRELATION,
    source="wertek.ai.vibration_classifier",
)
publish(recovery)
print()

# -- Summary ------------------------------------------------------
print("=" * 60)
print(f"  Published {len(published)} IAES events")
print(f"  correlation_id: {CORRELATION}")
print(f"  Event chain: measurement -> health(warning) -> health(critical) -> work_order -> recovery")
print("=" * 60)
