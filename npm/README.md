# @iaes/sdk

> TypeScript/JavaScript SDK for the Industrial Asset Event Standard.

[![npm](https://img.shields.io/npm/v/@iaes/sdk)](https://www.npmjs.com/package/@iaes/sdk)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

Create, serialize, validate, and publish industrial asset events using the [IAES v1.2 specification](https://iaes.dev).

## Install

```bash
npm install @iaes/sdk
```

## Quick Start

```ts
import { AssetMeasurement, IaesClient } from "@iaes/sdk";

// Create an event
const event = new AssetMeasurement({
  asset_id: "MOTOR-001",
  measurement_type: "vibration_velocity",
  value: 4.2,
  unit: "mm/s",
  source: "acme.sensors.plant1",
});

// Serialize to IAES wire format
const payload = JSON.stringify(event); // toJSON() called automatically

// Publish to any IAES-compatible endpoint
const client = new IaesClient("https://your-endpoint.example.com", {
  apiKey: "your-api-key",
});
const result = await client.publish(event);
```

## Event Types

| Event Type | Class | Purpose |
|------------|-------|---------|
| `asset.measurement` | `AssetMeasurement` | Sensor reading (vibration, temperature, pressure, power factor, THD...) |
| `asset.health` | `AssetHealth` | AI diagnosis or expert assessment (health index, fault, RUL) |
| `maintenance.work_order_intent` | `WorkOrderIntent` | Intent to create a work order |
| `maintenance.completion` | `MaintenanceCompletion` | Work order completion acknowledgment |
| `asset.hierarchy` | `AssetHierarchy` | Asset hierarchy sync (org > plant > area > equipment) |
| `sensor.registration` | `SensorRegistration` | Sensor discovery and lifecycle |
| `maintenance.spare_part_usage` | `SparePartUsage` | Spare parts consumed during maintenance |

## Examples

### Vibration measurement with ISO 17359 metadata

```ts
import { AssetMeasurement, UnitsQualifier } from "@iaes/sdk";

const event = new AssetMeasurement({
  asset_id: "MOTOR-001",
  measurement_type: "vibration_velocity",
  value: 4.2,
  unit: "mm/s",
  units_qualifier: UnitsQualifier.RMS,
  sampling_rate_hz: 25600,
  acquisition_duration_s: 1.0,
  source: "acme.sensors",
});
```

### AI health diagnosis

```ts
import { AssetHealth, Severity, ISO13374Status } from "@iaes/sdk";

const event = new AssetHealth({
  asset_id: "MOTOR-001",
  health_index: 0.16,
  severity: Severity.CRITICAL,
  failure_mode: "bearing_inner_race",
  rul_days: 5,
  recommended_action: "Replace bearing immediately",
  iso_13374_status: ISO13374Status.UNACCEPTABLE,
  iso_14224: {
    mechanism_code: "1.1",
    cause_code: "1",
    detection_method: "VIB",
  },
});
```

### Energy / power quality

```ts
import { AssetMeasurement } from "@iaes/sdk";

const pfEvent = new AssetMeasurement({
  asset_id: "SUBSTATION-A",
  measurement_type: "power_factor",
  value: 0.82,
  unit: "ratio",
  source: "ion8650.meter_01",
});

const thdEvent = new AssetMeasurement({
  asset_id: "SUBSTATION-A",
  measurement_type: "thd_voltage",
  value: 6.3,
  unit: "%",
  source: "ion8650.meter_01",
});
```

### Work order intent

```ts
import { WorkOrderIntent, WorkOrderPriority } from "@iaes/sdk";

const event = new WorkOrderIntent({
  asset_id: "MOTOR-001",
  title: "Replace bearing DE — AI diagnosis critical",
  priority: WorkOrderPriority.HIGH,
  triggered_by: "ai_diagnosis",
  recommended_due_days: 3,
  source_event_id: "<health_event_id>",
});
```

## Publishing Events

### Client instance (recommended)

```ts
import { IaesClient } from "@iaes/sdk";

const client = new IaesClient("https://your-endpoint.example.com", {
  apiKey: "your-api-key",
  timeout: 15000,       // ms, default 30000
  ingestPath: "/api/v1/iaes/ingest", // default
});

// Single event
const result = await client.publish(event);

// Batch
const results = await client.publishBatch([event1, event2, event3]);
```

### Convenience function

```ts
import { publish, AssetMeasurement } from "@iaes/sdk";

const event = new AssetMeasurement({ /* ... */ });
const result = await publish("https://your-endpoint.example.com", event, "your-api-key");
```

## Deserialization

```ts
import { fromJSON } from "@iaes/sdk";

const wire = JSON.parse(mqttMessage);
const event = fromJSON(wire); // Returns correct class instance
```

## Enums

All enums accept either the enum constant or a plain string:

```ts
new AssetHealth({ asset_id: "M-001", severity: Severity.CRITICAL });
new AssetHealth({ asset_id: "M-001", severity: "critical" }); // also works
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

## Type Exports

All init types are exported for typed construction:

```ts
import type { AssetMeasurementInit, AssetHealthInit } from "@iaes/sdk";
import type { IaesClientOptions, IngestResponse } from "@iaes/sdk";
import type { IAESEnvelope, AssetIdentity } from "@iaes/sdk";
```

## Zero Dependencies

The core SDK uses only Node.js built-in `crypto`. No runtime dependencies.

Optional: install `ajv` for JSON Schema validation.

## Cross-Language Compatibility

Both Python and TypeScript SDKs produce identical wire format and identical `content_hash` for the same data. Events created in Python validate in TypeScript and vice versa.

## Links

- [IAES Specification](https://iaes.dev) — Full spec, schemas, and examples
- [Python SDK](https://pypi.org/project/iaes/) — `pip install iaes`
- [Node-RED](https://flows.nodered.org/node/node-red-contrib-iaes) — `npm install node-red-contrib-iaes`
- [GitHub](https://github.com/wertek-ai/iaes)

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

---

*IAES v1.2 — March 2026*
