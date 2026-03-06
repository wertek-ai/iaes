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

## Terminology

| Term | Definition |
|------|-----------|
| **Event** | A self-contained JSON object describing something that happened to an industrial asset. |
| **Producer** | Any system that creates IAES events — sensor gateways, AI engines, rule engines, human inspectors, SCADA systems. |
| **Consumer** | Any system that receives and acts on IAES events — CMMS, historians, dashboards, digital twin platforms. |
| **Envelope** | The common wrapper fields shared by all IAES events (spec_version, event_type, event_id, etc.). |
| **Correlation** | A group of related events sharing the same `correlation_id`, representing a single observation-to-action flow. |
| **Source** | A dot-notation string identifying the producer of an event (e.g. `wertek.ai.vibration`, `operator.field_assessment`). |
| **Intent** | A declaration that an action should be considered, without prescribing how the consumer should act. Used in `maintenance.work_order_intent`. |
| **Health Index** | A normalized 0-1 score representing asset condition (0 = failed, 1 = healthy). |
| **RUL** | Remaining Useful Life — estimated days until the asset requires intervention. |

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

## Producer Guidelines

Systems that emit IAES events MUST follow these rules:

### Required behavior

1. **Set all required envelope fields.** Every event MUST include `spec_version`, `event_type`, `event_id`, `correlation_id`, `timestamp`, `source`, `asset` (with at least `asset_id`), and `data`.

2. **Generate unique `event_id` values.** Each event MUST have a globally unique `event_id` (UUID v4 recommended). Never reuse an `event_id` across events.

3. **Use dot-notation for `source`.** The `source` field MUST follow the pattern `vendor.system[.subsystem]`. Examples: `wertek.ai.vibration`, `banner.dxm100`, `operator.manual_inspection`. Use lowercase, alphanumeric characters, dots, and underscores only.

4. **Use ISO 8601 for timestamps.** The `timestamp` field MUST be in UTC with timezone designator (e.g. `2026-03-06T17:50:17Z`).

5. **Do not assume consumer behavior.** A `maintenance.work_order_intent` declares intent — the producer MUST NOT assume the consumer will create a work order, or create it in any specific format.

### Recommended behavior

1. **Set `correlation_id` to group related events.** When a measurement triggers a diagnosis that triggers a work order intent, all three events SHOULD share the same `correlation_id`.

2. **Set `source_event_id` for causal chains.** When an event is caused by another event (e.g. a health assessment caused by a measurement), set `source_event_id` to the `event_id` of the cause.

3. **Compute `content_hash` for deduplication.** Producers SHOULD compute `content_hash` as the first 16 characters of the SHA-256 hex digest of the serialized `data` payload (canonical JSON, sorted keys).

4. **Include `asset_name`, `plant`, and `area` when available.** These fields are optional but significantly improve human readability in logs, dashboards, and audit trails.

5. **Use standard `failure_mode` values when possible.** Common values: `bearing_inner_race`, `bearing_outer_race`, `misalignment`, `unbalance`, `looseness`, `cavitation`, `overheating`, `electrical_fault`. Custom values are allowed.

## Consumer Guidelines

Systems that receive IAES events MUST follow these rules:

### Required behavior

1. **Tolerate unknown fields.** Consumers MUST ignore fields in `data` that they do not recognize. Never reject an event because it contains extra fields. This is essential for forward compatibility.

2. **Tolerate unknown `event_type` values.** If a consumer receives an event with an `event_type` it does not support (e.g. a future `asset.hierarchy`), it MUST NOT error. It MAY log the event and skip processing.

3. **Validate `spec_version`.** Consumers SHOULD check `spec_version` and MAY reject events from unsupported major versions.

### Recommended behavior

1. **Deduplicate using `content_hash`.** Consumers SHOULD detect duplicate events using the combination of `content_hash` + `asset.asset_id` + `event_type`. If `content_hash` is not present, fall back to `event_id` uniqueness.

2. **Use `correlation_id` to reconstruct flows.** Consumers that display or analyze event chains SHOULD group events by `correlation_id` and order them by `timestamp`.

3. **Use `source_event_id` for traceability.** When displaying a work order intent, consumers SHOULD link back to the health event that triggered it (via `source_event_id`).

4. **Map severity to native priority.** Consumers that create native objects (work orders, notifications) SHOULD map IAES severity levels to their native priority system. A suggested default mapping:

| IAES severity | SAP PM | MaintainX | Odoo | General |
|---------------|--------|-----------|------|---------|
| `info` | — (no action) | — | — | — |
| `low` | Priority 4 | LOW | 0 (Very Urgent: No) | Low |
| `medium` | Priority 3 | MEDIUM | 1 (Normal) | Medium |
| `high` | Priority 2 | HIGH | 2 (Urgent) | High |
| `critical` | Priority 1 | HIGH | 3 (Very Urgent) | Critical |

5. **Respect intent semantics.** A `maintenance.work_order_intent` is a suggestion, not a command. Consumers MAY apply filters, rules, or approval workflows before creating native work orders. The consumer is the authority on what gets created in its system.

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

## Versioning

IAES uses semantic versioning for the specification itself:

- **`spec_version`** in every event envelope identifies which version of the spec was used to produce it.
- **Minor versions** (1.1, 1.2) add new optional fields, new event types, or new `triggered_by` values. They never remove existing fields or change required fields. Consumers built for 1.0 SHOULD accept events from 1.x without error.
- **Major versions** (2.0) may introduce breaking changes: removing fields, changing required fields, renaming event types, or changing envelope structure. Consumers MAY reject events from unsupported major versions.
- **Producers** MUST set `spec_version` to the version they implement.
- **Consumers** SHOULD accept events where the major version matches, even if the minor version is higher than what they support.

### Version history

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | March 2026 | Initial release. 3 event types, common envelope, JSON Schema. |

## License

IAES is an open specification licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Implementations may be proprietary.

---

*IAES v1.0 — March 2026*
*Created by the [Wertek AI](https://wertek.ai) team.*
*Reference implementation: [Wertek Integration Framework](https://github.com/wertek-ai/wertek-integrations)*
