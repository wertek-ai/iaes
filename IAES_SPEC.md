# IAES — Industrial Asset Event Standard v1.0

> A vendor-neutral event format for industrial asset intelligence.

## Purpose

IAES defines how industrial asset signals, diagnoses, and maintenance intents are represented and transferred across heterogeneous operational systems.

IAES is NOT a product. It is a data contract. Any system — sensor platform, AI engine, CMMS, historian, or dashboard — can produce or consume IAES events without knowing the implementation details of the other side.

## Principles

1. **Vendor neutrality** — No dependency on SAP, PI System, Odoo, or any specific vendor.
2. **Legacy compatibility** — Events map cleanly to CMMS, historians, SCADA, and IoT platforms.
3. **Event-oriented** — Each object represents something that happened (measurement, diagnosis, intent).
4. **Complete traceability** — Every event traces back to its origin via `event_id`, `correlation_id`, `source_event_id`.
5. **Extensibility** — The `data` payload and `metadata` field allow new fields without breaking consumers.

## Common Envelope

Every IAES event shares this envelope:

```json
{
  "spec_version": "1.0",
  "event_type": "asset.health",
  "event_id": "uuid",
  "correlation_id": "uuid",
  "source_event_id": "uuid | null",
  "timestamp": "ISO 8601",
  "source": "vendor.system.subsystem",
  "content_hash": "sha256_16char",
  "asset": {
    "asset_id": "string",
    "asset_name": "string | null",
    "plant": "string | null",
    "area": "string | null"
  },
  "data": {}
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `spec_version` | string | yes | IAES spec version (currently `"1.0"`) |
| `event_type` | string | yes | Dot-notation event type |
| `event_id` | UUID | yes | Unique identifier for this event |
| `correlation_id` | UUID | yes | Groups related events in a single flow |
| `source_event_id` | UUID | no | References the originating event |
| `timestamp` | ISO 8601 | yes | When the event occurred |
| `source` | string | yes | Dot-notation producer identity (e.g. `wertek.ai.diagnosis`, `operator.manual_inspection`) |
| `content_hash` | string | no | SHA-256 prefix (16 chars) of `data` payload for dedup |
| `asset` | object | yes | Asset identity (see Asset Identity) |
| `data` | object | yes | Event-specific payload |

### Asset Identity

```json
{
  "asset_id": "MOTOR-001",
  "asset_name": "Motor Bomba P-101",
  "plant": "Pesqueria",
  "area": "Turbinas"
}
```

The standard deliberately does NOT define a full asset hierarchy. Different organizations model hierarchies differently (ISO 14224, ISA-95, custom). IAES only requires enough context to identify the asset.

## Event Types (v1.0)

### `asset.measurement`

A physical sensor reading.

```json
{
  "event_type": "asset.measurement",
  "data": {
    "measurement_type": "vibration_rms",
    "value": 4.2,
    "unit": "mm/s",
    "sensor_id": "SENSOR-045",
    "location": "bearing_drive_end"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `measurement_type` | string | yes | Type (vibration_velocity, temperature, current, etc.) |
| `value` | number | yes | Numeric value |
| `unit` | string | yes | Engineering unit |
| `sensor_id` | string | no | Physical sensor identifier |
| `location` | string | no | Measurement point on the asset |

### `asset.health`

AI diagnosis / health state change. Includes recommended action.

```json
{
  "event_type": "asset.health",
  "data": {
    "health_index": 0.16,
    "anomaly_score": 0.92,
    "severity": "critical",
    "failure_mode": "bearing_inner_race",
    "fault_confidence": 0.87,
    "rul_days": 5,
    "recommended_action": "Replace bearing immediately",
    "estimated_downtime_hours": 4
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `health_index` | float 0-1 | yes | Normalized health (0 = failed, 1 = healthy) |
| `anomaly_score` | float 0-1 | no | Probability of anomaly |
| `severity` | enum | yes | info, low, medium, high, critical |
| `failure_mode` | string | no | Classified fault type |
| `fault_confidence` | float 0-1 | no | Classification confidence |
| `rul_days` | integer | no | Remaining Useful Life in days |
| `recommended_action` | string | no | Human-readable action suggestion |
| `estimated_downtime_hours` | float | no | Estimated repair duration |

### `maintenance.work_order_intent`

Declares the INTENT to create a work order. The consumer decides whether and how to act.

```json
{
  "event_type": "maintenance.work_order_intent",
  "data": {
    "title": "Bearing failure predicted",
    "description": "Inner race defect detected by AI diagnosis",
    "priority": "critical",
    "recommended_due_days": 3,
    "triggered_by": "alert"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Work order title |
| `description` | string | no | Detailed description |
| `priority` | enum | yes | low, medium, high, emergency |
| `recommended_due_days` | integer | no | Suggested deadline in days |
| `triggered_by` | string | no | What caused this intent (alert, schedule, manual) |

## Severity Standard

IAES defines five severity levels:

| Level | Meaning |
|-------|---------|
| `info` | Informational, no action needed |
| `low` | Minor, schedule for next planned maintenance |
| `medium` | Moderate, plan intervention within weeks |
| `high` | Significant, plan intervention within days |
| `critical` | Immediate action required |

## Idempotency

Every event includes:
- `event_id` — unique, never reused
- `content_hash` — SHA-256 of the `data` payload (16-char prefix)
- `correlation_id` — groups related events in a flow

Consumers SHOULD use `content_hash` + `asset.asset_id` + `event_type` to detect duplicate events.

## Producers

IAES events can originate from any source — not just AI systems:

| Source | Example `source` value | Typical events |
|--------|----------------------|----------------|
| AI diagnosis engine | `wertek.ai.vibration` | `asset.health` |
| Rule/threshold engine | `acme.rule_engine` | `asset.health` |
| Sensor gateway | `banner.dxm100` | `asset.measurement` |
| Manual inspection | `operator.manual_inspection` | `asset.health`, `asset.measurement` |
| Technician assessment | `operator.field_assessment` | `asset.health` |
| Lab analysis | `lab.oil_analysis` | `asset.measurement` |
| SCADA/PLC | `scada.plc_01` | `asset.measurement` |

The `source` field is what makes IAES vendor-neutral. A technician with a stethoscope and an AI model both produce the same `asset.health` event — the consumer doesn't need to know the difference.

## Typical Flow

```
Observation (sensor, AI, or human expert)
    |
    v
asset.measurement
    |
    v
Diagnosis (AI engine, rule engine, or expert assessment)
    |
    v
asset.health
    |
    v
maintenance.work_order_intent
    |
    v
Connector Adapter (SAP / Odoo / MaintainX / Fracttal / PI System)
```

## System Compatibility

| System | IAES Mapping |
|--------|-------------|
| SAP PM | Maintenance Notification / Order |
| PI System | Tag value writes |
| AVEVA Data Hub | SDS Stream writes |
| Odoo | maintenance.request |
| MaintainX | User Variables |
| Fracttal | Custom fields + OT |
| Grafana | Dashboard metrics |
| Any MQTT broker | JSON payload |

## Future (v1.1)

Planned additional event types:
- `asset.hierarchy` — Full asset tree sync
- `sensor.registration` — Sensor discovery and onboarding
- `maintenance.completion` — Work order completion acknowledgment
- `maintenance.spare_part_usage` — Parts consumed during maintenance

## License

IAES is an open specification. Implementations may be proprietary.

---

*IAES v1.0 — March 2026*
*Reference implementation: Wertek AI Integration Framework*
