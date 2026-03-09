# IAES — Industrial Asset Event Standard

> A vendor-neutral event format for industrial asset measurements, diagnoses, and maintenance intents.

[![PyPI](https://img.shields.io/pypi/v/iaes)](https://pypi.org/project/iaes/)
[![npm](https://img.shields.io/npm/v/@iaes/sdk)](https://www.npmjs.com/package/@iaes/sdk)
[![Node-RED](https://img.shields.io/npm/v/node-red-contrib-iaes?label=node-red)](https://flows.nodered.org/node/node-red-contrib-iaes)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

Industrial systems speak different languages. A vibration sensor outputs raw waveforms. An AI model outputs health scores. SAP expects maintenance notifications. PI System expects tag values. MaintainX expects user variables.

IAES provides the **neutral layer in between** — one event format that any producer can emit and any consumer can understand.

```
Sensors --> Intelligence --> IAES --> Connectors --> Enterprise Systems
```

## Install

```bash
pip install iaes                      # Python
npm install @iaes/sdk                 # TypeScript / Node.js
npm install node-red-contrib-iaes     # Node-RED
```

## Publish Events

The SDK includes a `Client` that sends IAES events to any compliant endpoint via HTTPS.

**Python:**

```python
from iaes import Client, AssetMeasurement

client = Client("https://your-endpoint.example.com", api_key="your-key")
event = AssetMeasurement(
    asset_id="MOTOR-001",
    measurement_type="vibration_velocity",
    value=4.2,
    unit="mm/s",
    source="acme.sensors.plant1",
)
result = client.publish(event)
```

**TypeScript:**

```ts
import { IaesClient, AssetMeasurement } from "@iaes/sdk";

const client = new IaesClient("https://your-endpoint.example.com", {
  apiKey: "your-key",
});
const event = new AssetMeasurement({
  asset_id: "MOTOR-001",
  measurement_type: "vibration_velocity",
  value: 4.2,
  unit: "mm/s",
  source: "acme.sensors.plant1",
});
const result = await client.publish(event);
```

The endpoint URL is any IAES-compliant receiver — your own backend, a cloud broker, or a third-party integration.

## Examples

### Vibration measurement

```python
from iaes import AssetMeasurement

event = AssetMeasurement(
    asset_id="MOTOR-001",
    measurement_type="vibration_velocity",
    value=4.2,
    unit="mm/s",
    source="acme.sensors.plant1",
    units_qualifier="rms",           # ISO 17359
    sampling_rate_hz=25600,
)
payload = event.to_dict()  # IAES wire format, ready for json.dumps()
```

```typescript
import { AssetMeasurement } from "@iaes/sdk"

const event = new AssetMeasurement({
  asset_id: "MOTOR-001",
  measurement_type: "vibration_velocity",
  value: 4.2,
  unit: "mm/s",
  source: "acme.sensors.plant1",
  units_qualifier: "rms",
  sampling_rate_hz: 25600,
})
const payload = JSON.stringify(event)  // toJSON() called automatically
```

### Energy / power quality

```python
from iaes import AssetMeasurement

pf_event = AssetMeasurement(
    asset_id="SUBSTATION-A",
    measurement_type="power_factor",
    value=0.82,
    unit="ratio",
    source="ion8650.meter_01",
)

thd_event = AssetMeasurement(
    asset_id="SUBSTATION-A",
    measurement_type="thd_voltage",
    value=6.3,
    unit="%",
    source="ion8650.meter_01",
)
```

### AI health diagnosis

```python
from iaes import AssetHealth, Severity

event = AssetHealth(
    asset_id="MOTOR-001",
    health_index=0.16,
    severity=Severity.CRITICAL,
    failure_mode="bearing_inner_race",
    rul_days=5,
    recommended_action="Replace bearing immediately",
    source="ai.vibration_model",
    iso_13374_status="unacceptable",   # ISO 13374
    iso_14224={                         # ISO 14224
        "mechanism_code": "1.1",
        "cause_code": "1",
        "detection_method": "VIB",
    },
)
```

### Work order intent

```python
from iaes import WorkOrderIntent

event = WorkOrderIntent(
    asset_id="MOTOR-001",
    title="Replace bearing DE — AI diagnosis critical",
    priority="high",
    triggered_by="ai_diagnosis",
    recommended_due_days=3,
    source="ai.vibration_model",
    source_event_id="<health_event_id>",  # links to the diagnosis
)
```

### Maintenance completion

```python
from iaes import MaintenanceCompletion

event = MaintenanceCompletion(
    asset_id="MOTOR-001",
    work_order_id="WO-2026-0042",
    status="completed",
    actual_duration_seconds=7200,
    failure_confirmed=True,
    failure_mode="bearing_inner_race",
    source="cmms.sap_pm",
)
```

## Validate

```python
from iaes import validate, ValidationError

try:
    validate(event.to_dict())
    print("Valid IAES event")
except ValidationError as e:
    print(e)
```

Requires: `pip install iaes[validate]`

## Deserialize

```python
import json
from iaes import from_dict

# Any IAES envelope -> correct model instance
wire = json.loads(mqtt_message)
event = from_dict(wire)  # AssetMeasurement, AssetHealth, etc.
print(event.asset_id, event.value)
```

## Event Types (v1.2)

| Event Type | Python | TypeScript | Purpose |
|------------|--------|------------|---------|
| `asset.measurement` | `AssetMeasurement` | `AssetMeasurement` | Sensor reading (vibration, temperature, pressure, current, power factor, THD...) |
| `asset.health` | `AssetHealth` | `AssetHealth` | AI diagnosis or expert assessment (health index, fault, RUL) |
| `maintenance.work_order_intent` | `WorkOrderIntent` | `WorkOrderIntent` | Intent to create a work order |
| `maintenance.completion` | `MaintenanceCompletion` | `MaintenanceCompletion` | Work order completion acknowledgment |
| `asset.hierarchy` | `AssetHierarchy` | `AssetHierarchy` | Asset hierarchy sync (org > plant > area > equipment) |
| `sensor.registration` | `SensorRegistration` | `SensorRegistration` | Sensor discovery and lifecycle |
| `maintenance.spare_part_usage` | `SparePartUsage` | `SparePartUsage` | Spare parts consumed during maintenance |

## Enums

All enums accept either the enum constant or a plain string:

```python
AssetHealth(asset_id="M-001", severity=Severity.CRITICAL)
AssetHealth(asset_id="M-001", severity="critical")  # also works
```

| Enum | Values |
|------|--------|
| `Severity` | info, low, medium, high, critical |
| `MeasurementType` | vibration_velocity, vibration_acceleration, temperature, current, voltage, power, pressure, flow, speed, power_factor, thd_voltage, thd_current, frequency, ... |
| `UnitsQualifier` | rms, peak, peak_to_peak, average, true_rms |
| `ISO13374Status` | unknown, normal, satisfactory, unsatisfactory, unacceptable, imminent_failure, failed |
| `WorkOrderPriority` | low, medium, high, emergency |
| `CompletionStatus` | completed, partially_completed, cancelled, deferred |
| `HierarchyLevel` | organization, plant, area, equipment |
| `RelationshipType` | parent_of, child_of, sibling_of, depends_on |
| `RegistrationStatus` | discovered, registered, calibrated, decommissioned |

## Wire Format

Every event serializes to the same envelope structure:

```json
{
  "spec_version": "1.2",
  "event_type": "asset.measurement",
  "event_id": "a9e3c4b2-...",
  "correlation_id": "3b2f9d8c-...",
  "timestamp": "2026-03-08T12:00:00+00:00",
  "source": "acme.sensors.plant1",
  "content_hash": "8a3f9c2e1b4d7e6f",
  "asset": {
    "asset_id": "MOTOR-001",
    "asset_name": "Motor Bomba P-101",
    "plant": "Pesqueria",
    "area": "Turbinas"
  },
  "data": {
    "measurement_type": "vibration_velocity",
    "value": 4.2,
    "unit": "mm/s",
    "units_qualifier": "rms",
    "sampling_rate_hz": 25600
  }
}
```

`content_hash` is a 16-char SHA-256 prefix of the `data` payload, computed identically in Python and TypeScript for cross-language idempotency.

## ISO Standards Alignment

| Standard | IAES Fields | Purpose |
|----------|-------------|---------|
| **ISO 17359** | `units_qualifier`, `sampling_rate_hz`, `acquisition_duration_s` | Condition monitoring measurement metadata |
| **ISO 13374** | `iso_13374_status` | 7-level condition status (normal to failed) |
| **ISO 14224** | `iso_14224` object | Failure mechanism, cause, and detection codes |
| **ISO 55000** | Architectural | Asset management principles embedded in design |

All ISO fields are optional. v1.0/v1.1 events remain fully valid.

## Zero Dependencies

The core SDK uses only standard library. No runtime dependencies.

| | Core | Validation |
|-|------|------------|
| **Python** | stdlib only | `pip install iaes[validate]` adds `jsonschema` |
| **TypeScript** | Node.js `crypto` only | `ajv` optional |

## Cross-Language Compatibility

Both SDKs produce identical wire format and identical `content_hash` for the same data. Events created in Python validate in TypeScript and vice versa. This is tested on every commit.

## Node-RED

[`node-red-contrib-iaes`](https://flows.nodered.org/node/node-red-contrib-iaes) provides 7 nodes for visual IAES workflows:

| Node | Purpose |
|------|---------|
| **iaes-measurement** | Create `asset.measurement` events from sensor inputs |
| **iaes-health** | Create `asset.health` events from AI models or expert rules |
| **iaes-work-order** | Create `maintenance.work_order_intent` events |
| **iaes-validate** | Validate any IAES envelope against JSON Schema |
| **iaes-sparkplug** | Bridge Sparkplug B payloads to/from IAES format |
| **iaes-publish** | Publish IAES events to any compliant HTTP endpoint |
| **iaes-route** | Route events by type, severity, or custom expressions |

```bash
npm install node-red-contrib-iaes
```

## Resources

- **[IAES_SPEC.md](IAES_SPEC.md)** — Full specification
- **[schema/](schema/)** — 8 JSON Schema files
- **[examples/](examples/)** — 10 JSON examples
- **[iaes.dev](https://iaes.dev)** — Website

## Design Principles

1. **Vendor neutrality** — No dependency on any specific platform or system
2. **Legacy compatibility** — Maps cleanly to CMMS, historians, SCADA, IoT
3. **Event-oriented** — Each object represents something that happened
4. **Complete traceability** — `event_id` + `correlation_id` + `source_event_id` chain
5. **Extensibility** — `data` payload allows new fields without breaking consumers

## System Compatibility

| System | IAES Mapping |
|--------|-------------|
| SAP PM | Maintenance Notification / Order |
| PI System / AVEVA | Tag value writes / SDS streams |
| Odoo | maintenance.request |
| MaintainX | User Variables |
| Fracttal | Custom fields + OT |
| Node-RED | [`node-red-contrib-iaes`](https://flows.nodered.org/node/node-red-contrib-iaes) — 7 nodes |
| MQTT / Kafka | JSON payload on any topic |

## License

IAES is an open specification. The specification text and JSON schemas are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Implementations may use any license.

---

*IAES v1.2 — March 2026*
