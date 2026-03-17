"""
IAES Example: Alert Fatigue Reduction
======================================

Demonstrates how IAES correlation_id reduces 30+ raw threshold
alerts into 2 meaningful incidents.

Traditional system:  30 alerts  -> 30 emails/notifications -> alert fatigue
With IAES:           30 events  -> 2 correlated incidents  -> actionable

The key: correlation_id groups related events into a single incident chain.
An IncidentStateTracker (IAES v1.3) manages the state machine:
    NORMAL -> ONSET -> ESCALATION -> (suppressed repeats) -> RECOVERY

Run:
    pip install iaes
    python alert_fatigue.py
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
published = []

# Two independent failure modes on the same pump
CORR_BEARING = f"{ASSET}:bearing_outer_race"
CORR_THERMAL = f"{ASSET}:thermal_overload"

# ISO 17359 thresholds
VIB_WARNING = 7.1    # mm/s RMS -- Zone C
VIB_CRITICAL = 11.2  # mm/s RMS -- Zone D
TEMP_WARNING = 85.0   # degrees C -- bearing housing
CURR_WARNING = 1.15   # x FLA -- overload


def publish(event, pretty=True):
    """Print IAES event JSON to stdout (swap with Client for real endpoint)."""
    payload = event.to_dict()
    published.append(payload)
    indent = 2 if pretty else None
    print(json.dumps(payload, indent=indent, default=str))


traditional_alert_count = 0

print("=" * 70)
print("  IAES Alert Fatigue Demo")
print("  30 raw sensor alerts  ->  2 correlated incidents")
print("=" * 70)
print()

# -- INCIDENT 1: Bearing degradation (vibration) ------------------
print("-" * 70)
print("  INCIDENT 1: Bearing Outer Race Degradation")
print(f"  correlation_id: {CORR_BEARING}")
print("-" * 70)
print()

# Phase A: 6 vibration readings crossing warning threshold
print("> Phase A: Warning-level vibration crossings (6 readings)")
print("-" * 50)
for i in range(6):
    vib = round(random.uniform(7.2, 9.5), 1)
    event = AssetMeasurement(
        asset_id=ASSET,
        asset_name="Cooling Water Pump",
        plant=PLANT,
        area=AREA,
        measurement_type="vibration_rms",
        value=vib,
        unit="mm/s",
        units_qualifier="rms",
        sampling_rate_hz=25600,
        correlation_id=CORR_BEARING,
        source="sensor.accelerometer.sku200",
    )
    publish(event, pretty=False)
    traditional_alert_count += 1
print()

# IAES: ONE health onset event (instead of 6 separate alerts)
print("  >> IAES ONSET: Single health event for all 6 crossings")
print("-" * 50)
onset = AssetHealth(
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
    correlation_id=CORR_BEARING,
    source="wertek.ai.vibration_classifier",
)
publish(onset)
print()

# Phase B: 8 more readings -- vibration escalating to critical
print("> Phase B: Critical vibration escalation (8 readings)")
print("-" * 50)
for i in range(8):
    vib = round(random.uniform(11.5, 15.0), 1)
    event = AssetMeasurement(
        asset_id=ASSET,
        asset_name="Cooling Water Pump",
        plant=PLANT,
        area=AREA,
        measurement_type="vibration_rms",
        value=vib,
        unit="mm/s",
        units_qualifier="rms",
        sampling_rate_hz=25600,
        correlation_id=CORR_BEARING,
        source="sensor.accelerometer.sku200",
    )
    publish(event, pretty=False)
    traditional_alert_count += 1
print()

# IAES: ONE escalation event
print("  >> IAES ESCALATION: Single health event for all 8 critical crossings")
print("-" * 50)
escalation = AssetHealth(
    asset_id=ASSET,
    health_index=0.16,
    severity=Severity.CRITICAL,
    failure_mode="bearing_outer_race",
    condition_trend=ConditionTrend.WORSENING,
    iso_13374_status="unacceptable",
    rul_days=3,
    recommended_action="Replace bearing immediately -- risk of seizure",
    correlation_id=CORR_BEARING,
    source="wertek.ai.vibration_classifier",
)
publish(escalation)
print()

# IAES: Auto work order
print("  >> IAES AUTO WORK ORDER: One WO for the entire incident")
print("-" * 50)
wo = WorkOrderIntent(
    asset_id=ASSET,
    asset_name="Cooling Water Pump",
    plant=PLANT,
    area=AREA,
    title="Replace outer race bearing -- PUMP-101",
    priority="critical",
    description=(
        "Vibration RMS exceeded Zone D (11.2 mm/s). "
        "AI diagnosis: bearing outer race defect. RUL: 3 days. "
        "18 threshold crossings correlated into single incident."
    ),
    correlation_id=CORR_BEARING,
    source="wertek.ai.auto_wo",
)
publish(wo)
print()

# Phase C: Recovery after maintenance
print("> Phase C: Post-maintenance recovery")
print("-" * 50)
recovery = AssetHealth(
    asset_id=ASSET,
    health_index=0.92,
    severity=Severity.INFO,
    failure_mode="bearing_outer_race",
    condition_trend=ConditionTrend.IMPROVING,
    iso_13374_status="normal",
    recommended_action="Bearing replaced. Asset returned to normal operation.",
    correlation_id=CORR_BEARING,
    source="wertek.ai.vibration_classifier",
)
publish(recovery)
print()

# -- INCIDENT 2: Thermal overload (temperature + current) ---------
print("-" * 70)
print("  INCIDENT 2: Thermal Overload")
print(f"  correlation_id: {CORR_THERMAL}")
print("-" * 70)
print()

# Phase A: 5 temperature + 4 current readings crossing thresholds
print("> Phase A: High temperature readings (5 readings)")
print("-" * 50)
for i in range(5):
    temp = round(random.uniform(87.0, 102.0), 1)
    event = AssetMeasurement(
        asset_id=ASSET,
        asset_name="Cooling Water Pump",
        plant=PLANT,
        area=AREA,
        measurement_type="temperature",
        value=temp,
        unit="degC",
        correlation_id=CORR_THERMAL,
        source="sensor.rtd.bearing_housing",
    )
    publish(event, pretty=False)
    traditional_alert_count += 1
print()

print("> Phase A (cont): High motor current (4 readings)")
print("-" * 50)
for i in range(4):
    current = round(random.uniform(1.16, 1.28), 2)
    event = AssetMeasurement(
        asset_id=ASSET,
        asset_name="Cooling Water Pump",
        plant=PLANT,
        area=AREA,
        measurement_type="motor_current",
        value=current,
        unit="x_FLA",
        correlation_id=CORR_THERMAL,
        source="sensor.ct.mcc_panel",
    )
    publish(event, pretty=False)
    traditional_alert_count += 1
print()

# IAES: ONE health event correlating temperature + current
print("  >> IAES ONSET: Single health event correlating temp + current")
print("-" * 50)
thermal_onset = AssetHealth(
    asset_id=ASSET,
    asset_name="Cooling Water Pump",
    plant=PLANT,
    area=AREA,
    health_index=0.40,
    severity=Severity.HIGH,
    failure_mode="thermal_overload",
    condition_trend=ConditionTrend.WORSENING,
    iso_13374_status="unsatisfactory",
    rul_days=7,
    recommended_action=(
        "Check cooling system, verify motor load. "
        "9 threshold crossings (5 temp + 4 current) correlated."
    ),
    correlation_id=CORR_THERMAL,
    source="wertek.ai.thermal_classifier",
)
publish(thermal_onset)
print()

# Recovery
print("> Phase B: Recovery after cooling fix")
print("-" * 50)
thermal_recovery = AssetHealth(
    asset_id=ASSET,
    health_index=0.88,
    severity=Severity.INFO,
    failure_mode="thermal_overload",
    condition_trend=ConditionTrend.IMPROVING,
    iso_13374_status="normal",
    recommended_action="Cooling restored. Motor current nominal.",
    correlation_id=CORR_THERMAL,
    source="wertek.ai.thermal_classifier",
)
publish(thermal_recovery)
print()

# -- Summary -------------------------------------------------------
total_events = len(published)
incidents = 2

print("=" * 70)
print("  RESULTS")
print("=" * 70)
print()
print(f"  Traditional system:")
print(f"    {traditional_alert_count} threshold crossings = {traditional_alert_count} separate alerts")
print(f"    -> {traditional_alert_count} emails, {traditional_alert_count} SMS, {traditional_alert_count} push notifications")
print(f"    -> Operator ignores most of them (alert fatigue)")
print()
print(f"  With IAES correlation_id:")
print(f"    {total_events} total IAES events published")
print(f"    -> {incidents} correlated incidents")
print(f"    -> 1 auto-generated work order")
print(f"    -> {round((1 - incidents / traditional_alert_count) * 100)}% alert reduction")
print()
print(f"  Incident chains:")
print(f"    1. {CORR_BEARING}  (18 events -> 1 incident + 1 WO)")
print(f"    2. {CORR_THERMAL}  (12 events -> 1 incident)")
print()
print(f"  Key: correlation_id groups related events across sensors,")
print(f"       failure modes, and time -- so operators see INCIDENTS,")
print(f"       not individual threshold crossings.")
print("=" * 70)
