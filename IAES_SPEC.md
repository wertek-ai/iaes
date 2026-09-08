# IAES — Industrial Asset Event Standard v2.0

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
| **Source** | A dot-notation string identifying the producer of an event (e.g. `vendor.vibration`, `operator.field_assessment`). |
| **Intent** | A declaration that an action should be considered, without prescribing how the consumer should act. Used in `maintenance.work_order_intent`. |
| **Health Index** | A normalized 0-1 score representing asset condition (0 = failed, 1 = healthy). |
| **RUL** | Remaining Useful Life — estimated days until the asset requires intervention. |

## Common Envelope

Every IAES event shares this envelope:

```json
{
  "spec_version": "1.3",
  "event_type": "asset.health",
  "event_id": "uuid",
  "correlation_id": "uuid",
  "source_event_id": "uuid | null",
  "batch_id": "string | null",
  "dataschema": "https://iaes.dev/schema/v2/asset.health",
  "timestamp": "RFC 3339",
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
| `spec_version` | string | yes | IAES spec version (`"1.0"` through `"1.4"`) |
| `dataschema` | URI | no | Canonical URI of the schema the `data` payload was written against (v1.4) |
| `event_type` | string | yes | Dot-notation event type, matching `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_.]*$`. Open: a producer MAY define its own (v1.4) |
| `event_id` | UUID | yes | Unique identifier for this event |
| `correlation_id` | UUID | yes | Groups related events in a single flow |
| `source_event_id` | UUID | no | References the originating event |
| `timestamp` | RFC 3339 | yes | When the event occurred |
| `source` | string | yes | Dot-notation producer identity (e.g. `vendor.diagnosis`, `operator.manual_inspection`) |
| `batch_id` | string | no | Groups events from a single batch operation (e.g. gateway poll, bulk sync) |
| `content_hash` | string | no | SHA-256 prefix (16 chars) of `data` payload for dedup |
| `asset` | object | yes | Asset identity (see Asset Identity) |
| `data` | object | yes | Event-specific payload |

### Asset Identity

```json
{
  "asset_id": "MOTOR-001",
  "asset_name": "Motor Bomba P-101",
  "plant": "Planta Norte",
  "area": "Turbinas"
}
```

The standard deliberately does NOT define a full asset hierarchy. Different organizations model hierarchies differently (ISO 14224, ISA-95, custom). IAES only requires enough context to identify the asset.

## Event Types

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
| `measurement_type` | string | yes | **Open.** Any published list of measurement types is ADVISORY and constrains nothing; a consumer MUST NOT reject an event because its value is not listed. |
| `measurement_type` (values) | string | — | Type (vibration_velocity, temperature, current, etc.) |
| `value` | number | yes | Numeric value |
| `unit` | string | yes | Engineering unit |
| `sensor_id` | string | no | Physical sensor identifier |
| `location` | string | no | Measurement point on the asset |
| `units_qualifier` | string | no | Signal processing method: `rms`, `peak`, `peak_to_peak`, `average`, `true_rms` (ISO 17359 §6.3, v1.2) |
| `sampling_rate_hz` | number | no | Sampling rate in Hz (v1.2) |
| `acquisition_duration_s` | number | no | Measurement acquisition window in seconds (v1.2) |

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
| `condition_trend` | string | no | Temporal trend of the condition: `worsening`, `stable`, `improving`. Indicates whether the assessed condition is deteriorating, holding steady, or getting better compared to the previous assessment. IAES's own vocabulary: any correspondence to an external standard is unverified and is not asserted. (v1.3; attribution withdrawn in 2.0) |
| `iso_13374_status` | string | no | Health status: `unknown`, `normal`, `satisfactory`, `unsatisfactory`, `unacceptable`, `imminent_failure`, `failed`. IAES's own vocabulary; the field name is retained for compatibility with 1.x (v1.2, see Appendix C) |
| `iso_14224` | object | no | ISO 14224 failure classification codes (v1.2, see Appendix B) |

### `maintenance.work_order_intent`

Declares the INTENT to create a work order. The consumer decides whether and how to act.

```json
{
  "event_type": "maintenance.work_order_intent",
  "data": {
    "title": "Bearing failure predicted",
    "description": "Inner race defect detected by AI diagnosis",
    "priority": "emergency",
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
| `triggered_by` | string | no | What caused this intent: `alert`, `schedule`, `manual`, `threshold`, `ai_diagnosis` |

> **Note: severity is not priority.** `severity` (on `asset.health`) represents the **condition of the asset**. `priority` (on `maintenance.work_order_intent`) represents the **urgency of the proposed response**. They are different catalogs that share the values `low`, `medium` and `high`, and mean different things by them. A producer MUST NOT present one as the other. Which urgency a condition deserves is the consumer's judgment, because the consumer knows what else is running.

### `maintenance.completion` (v1.1)

Acknowledges the completion of a work order. Links back to the original intent via `correlation_id`.

```json
{
  "event_type": "maintenance.completion",
  "data": {
    "status": "completed",
    "work_order_id": "WO-2026-0042",
    "actual_duration_seconds": 7200,
    "technician_id": "TECH-003",
    "checklist_completion_pct": 100,
    "completion_notes": "Bearing replaced. Post-repair vibration 0.8 mm/s.",
    "spare_parts_count": 1,
    "failure_confirmed": true,
    "failure_mode": "bearing_inner_race"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | enum | yes | completed, partially_completed, cancelled, deferred |
| `work_order_id` | string | yes | Identifier of the completed work order |
| `actual_duration_seconds` | integer | no | Actual time spent in seconds |
| `technician_id` | string | no | Identifier of the technician |
| `checklist_completion_pct` | float 0-100 | no | Percentage of checklist completed |
| `completion_notes` | string | no | Free-text notes from the technician |
| `spare_parts_count` | integer | no | Number of spare parts consumed (detail in `spare_part_usage` events) |
| `failure_confirmed` | boolean | no | Whether the predicted failure mode was confirmed |
| `failure_mode` | string | no | Confirmed or observed failure mode (see Appendix A) |
| `iso_14224` | object | no | ISO 14224 failure classification codes confirmed during maintenance (v1.2, see Appendix B) |

### `asset.hierarchy` (v1.1)

Synchronizes asset hierarchy structure across systems. Each event represents one node and its relationship.

```json
{
  "event_type": "asset.hierarchy",
  "data": {
    "hierarchy_level": "equipment",
    "relationship_type": "child_of",
    "parent_asset_id": "AREA-TURBINAS",
    "asset_type": "motor",
    "serial_number": "WEG-2024-78432",
    "manufacturer": "WEG",
    "model": "W22 Premium 75HP",
    "is_active": true
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hierarchy_level` | enum | yes | organization, plant, area, equipment |
| `relationship_type` | enum | yes | parent_of, child_of, sibling_of, depends_on |
| `parent_asset_id` | string | no | Identifier of the parent node |
| `asset_type` | string | no | Equipment type (motor, pump, compressor, etc.) |
| `serial_number` | string | no | Manufacturer serial number |
| `manufacturer` | string | no | Equipment manufacturer |
| `model` | string | no | Equipment model |
| `location` | string | no | Physical location description |
| `is_active` | boolean | no | Whether the asset is active/operational |

### `sensor.registration` (v1.1)

Sensor discovery, onboarding, and lifecycle tracking.

```json
{
  "event_type": "sensor.registration",
  "data": {
    "sensor_id": "MCSA-T41-001",
    "registration_status": "registered",
    "sensor_model": "Acme MCSA CT Module",
    "device_serial": "T41-2026-00042",
    "firmware_version": "1.0.3",
    "measurement_capabilities": ["current_waveform", "current_spectrum", "current_rms", "thd"],
    "calibration_date": "2026-03-05",
    "communication_protocol": "mqtt"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sensor_id` | string | yes | Unique sensor identifier |
| `registration_status` | enum | yes | discovered, registered, calibrated, decommissioned |
| `sensor_model` | string | no | Sensor hardware model |
| `device_serial` | string | no | Device serial number |
| `firmware_version` | string | no | Current firmware version |
| `measurement_capabilities` | string[] | no | Measurement types this sensor provides |
| `calibration_date` | RFC 3339 full-date | no | Last calibration date |
| `communication_protocol` | string | no | Protocol (mqtt, modbus_tcp, opcua, lorawan, etc.) |

### `maintenance.spare_part_usage` (v1.1)

Records spare parts consumed during a maintenance activity. Linked to the work order via `work_order_id` and to the completion event via `correlation_id`. There may be 0-N spare part usage events per work order.

```json
{
  "event_type": "maintenance.spare_part_usage",
  "data": {
    "work_order_id": "WO-2026-0042",
    "spare_part_id": "SP-SKF-6205",
    "quantity_used": 1,
    "part_number": "SKF 6205-2RS",
    "part_name": "Rodamiento rigido de bolas 6205-2RS",
    "unit_cost": 28.50,
    "currency": "USD",
    "total_cost": 28.50
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `work_order_id` | string | yes | Work order that consumed the part |
| `spare_part_id` | string | yes | Part identifier in the inventory system |
| `quantity_used` | number | yes | Quantity consumed (> 0) |
| `part_number` | string | no | Manufacturer part number |
| `part_name` | string | no | Human-readable part name |
| `unit_cost` | number | no | Cost per unit |
| `currency` | string | no | ISO 4217 currency code (USD, MXN, BRL) |
| `total_cost` | number | no | Total cost (quantity_used * unit_cost) |

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

IAES events are produced by systems capable of interpreting operational signals — not by the signals themselves.

A PLC, sensor, or gateway knows `vibration_rms = 4.6`. That is telemetry, not a diagnosis. IAES begins where interpretation begins: an AI model that classifies a bearing fault, a rule engine that triggers on a threshold, or a technician who hears cavitation.

### Intelligence layer producers

| Source | Example `source` value | Typical events |
|--------|----------------------|----------------|
| AI diagnosis engine | `vendor.vibration` | `asset.health` |
| Rule/threshold engine | `acme.rule_engine` | `asset.health` |
| Manual inspection | `operator.manual_inspection` | `asset.health`, `asset.measurement` |
| Technician assessment | `operator.field_assessment` | `asset.health` |
| Lab analysis | `lab.oil_analysis` | `asset.measurement` |
| Maintenance application | `vendor.cmms` | `maintenance.work_order_intent` |

### Signal sources (upstream of IAES)

Operational systems such as PLCs, SCADA platforms, sensor gateways, and historians typically emit raw signals or measurements. These are converted into IAES events by downstream intelligence layers.

```
Industrial Signals              IAES Events
(PLC / Sensors / SCADA)         (semantic, interpreted)
        │                               │
        ▼                               ▼
  Telemetry Layer               ┌──────────────┐
  (OPC UA / Modbus / MQTT)      │  CMMS        │
        │                       │  Dashboards   │
        ▼                       │  Historians   │
  Intelligence Layer     ──────>│  Integrations │
  (AI / rules / human)         └──────────────┘
```

An edge device MAY produce IAES events directly if it has sufficient intelligence (e.g. edge AI, embedded rule engine). But the typical flow is: signals are ingested by an intelligence layer, which then emits IAES events.

The `source` field is what makes IAES vendor-neutral. A technician with a stethoscope and an AI model both produce the same `asset.health` event — the consumer doesn't need to know the difference.

## Producer Guidelines

Systems that emit IAES events MUST follow these rules:

### Required behavior

1. **Set all required envelope fields.** Every event MUST include `spec_version`, `event_type`, `event_id`, `correlation_id`, `timestamp`, `source`, `asset` (with at least `asset_id`), and `data`.

2. **Generate unique `event_id` values.** Each event MUST have a globally unique `event_id` (UUID v4 recommended). Never reuse an `event_id` across events.

3. **Use dot-notation for `source`.** The `source` field MUST follow the pattern `vendor.system[.subsystem]`. Examples: `vendor.vibration`, `banner.dxm100`, `operator.manual_inspection`. Use lowercase, alphanumeric characters, dots, and underscores only.

4. **Use RFC 3339 for timestamps.** The `timestamp` field MUST be in UTC with timezone designator (e.g. `2026-03-06T17:50:17Z`). RFC 3339 is the profile of ISO 8601 that JSON Schema's `date-time` format is defined by; naming it means an implementer can read the exact document the constraint comes from, at no cost.

5. **Do not assume consumer behavior.** A `maintenance.work_order_intent` declares intent — the producer MUST NOT assume the consumer will create a work order, or create it in any specific format.

### Recommended behavior

1. **Set `correlation_id` to group related events.** When a measurement triggers a diagnosis that triggers a work order intent, all three events SHOULD share the same `correlation_id`.

2. **Set `source_event_id` for causal chains.** When an event is caused by another event (e.g. a health assessment caused by a measurement), set `source_event_id` to the `event_id` of the cause.

3. **An absent optional field is not an assertion.** A producer MUST omit an optional field it was not given rather than substitute a value for it. Writing `anomaly_score: 0.0` for a score nobody computed states something the producer does not know, and a consumer cannot tell it apart from a measured zero. Consumers MUST NOT read an absent optional field as a default.
4. **A custom `event_type` is allowed, and must look like one.** The published types are the interoperability defaults, not the limit: a producer MAY emit its own, provided it matches the dot-notation shape. Use a namespace you control (`acme.press_stroke`, not `asset.something`), and omit `dataschema`, since no schema is published for it.

4. **Set `dataschema` to the schema the payload was written against.** Producers SHOULD include it. The schema for a published event type is always `https://iaes.dev/schema/v<major>/<event_type>` for the major the event declares — `https://iaes.dev/schema/v2/<event_type>` in this release, so an SDK can derive it rather than ask for it. A producer using a custom `event_type` with no published schema MUST omit the field rather than point at a URI that does not resolve.

5. **Compute `content_hash` for deduplication.** Producers SHOULD compute `content_hash` as the first 16 characters of the SHA-256 hex digest of the serialized `data` payload (canonical JSON, sorted keys).

4. **Include `asset_name`, `plant`, and `area` when available.** These fields are optional but significantly improve human readability in logs, dashboards, and audit trails.

5. **Use standard `failure_mode` values when possible.** Common values: `bearing_inner_race`, `bearing_outer_race`, `misalignment`, `unbalance`, `looseness`, `cavitation`, `overheating`, `electrical_fault`. Custom values are allowed.

## Consumer Guidelines

Systems that receive IAES events MUST follow these rules:

### Required behavior

1. **Tolerate unknown fields.** Consumers MUST ignore fields in `data` that they do not recognize. Never reject an event because it contains extra fields. This is essential for forward compatibility.

3. **Tolerate unknown `event_type` values.** If a consumer receives an event with an `event_type` it does not support — a type published after it was built, or a producer's own — it MUST NOT error. It MAY log the event and skip processing.

3. **Validate `spec_version`.** Consumers SHOULD check `spec_version` and MAY reject events from unsupported major versions.

### Recommended behavior

1. **Do not require `dataschema`.** It is optional and MUST NOT be a reason to reject an event. When present, a consumer MAY use it to select the validator for the payload, and to tell which version of a contract the producer wrote against without asking. When absent, fall back to `event_type` and `spec_version`.

2. **Deduplicate using `content_hash`.** Consumers SHOULD detect duplicate events using the combination of `content_hash` + `asset.asset_id` + `event_type`. If `content_hash` is not present, fall back to `event_id` uniqueness.

2. **Use `correlation_id` to reconstruct flows.** Consumers that display or analyze event chains SHOULD group events by `correlation_id` and order them by `timestamp`.

3. **Use `source_event_id` for traceability.** When displaying a work order intent, consumers SHOULD link back to the health event that triggered it (via `source_event_id`).

4. **Map severity to your own priority scale.** Consumers that create native objects (work orders, notifications) SHOULD map IAES `severity` **to their own priority system**. The table below is a mapping *from* IAES severity *to* a target system's scale — it is **not** an equivalence between the two IAES catalogs, which are distinct. A suggested default:

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
asset.measurement ─── [batch_id groups gateway polls]
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
    |
    v
maintenance.completion ─── [technician closes WO]
    |
    v
maintenance.spare_part_usage ─── [0-N parts consumed]
```

All events in the chain share the same `correlation_id`. Each references its predecessor via `source_event_id`.

### Recovery Events

An `asset.health` event MAY represent recovery — when a previously abnormal condition returns to acceptable parameters. A recovery event uses the existing fields with values indicating normal operation:

```json
{
  "event_type": "asset.health",
  "data": {
    "health_index": 0.95,
    "severity": "info",
    "iso_13374_status": "normal",
    "condition_trend": "improving",
    "recommended_action": "Condition returned to normal. Continue routine monitoring."
  }
}
```

Recovery events SHOULD reference the original onset event via `source_event_id` and share the same `correlation_id`. This enables consumers to compute Mean Time To Recovery (MTTR) and close open alerts automatically.

> Detailed emission and transition guidance is not yet published. Until it is, the rules above
> are the whole of what this specification says about when to emit.

## Event Type Usage Guide

When to use each event type, who produces it, and who consumes it.

| Event Type | Typical Producer | Typical Consumer | Use When | Do NOT Use When |
|------------|-----------------|------------------|----------|-----------------|
| `asset.measurement` | Sensor gateway, edge device, historian bridge | AI/ML engine, rule engine, data lake, digital twin | A sensor reading needs to be shared across systems (vibration, temperature, power factor, THD, current, voltage, pressure) | Storing raw waveforms (use a blob store). Logging routine telemetry internally (use your time-series DB directly). |
| `asset.health` | AI model, rule engine, expert inspector, SCADA alarm mapper | CMMS (work order creation), dashboard (KPIs), alert engine, incident tracker | An actionable condition assessment exists — fault detected, health index calculated, alarm threshold crossed, recovery confirmed | Routine "all clear" polling. Use only when a condition state changes or is actively abnormal. |
| `maintenance.work_order_intent` | AI engine, alert rule, human operator, planning system | CMMS (SAP PM, Odoo, MaintainX, Fracttal), dispatcher, approval workflow | A work order SHOULD be created based on a diagnosis, alert, or schedule | Acknowledging work already in progress (use `maintenance.completion`). |
| `maintenance.completion` | CMMS, mobile app, technician handoff | AI model (retraining feedback), historian (close loop), dashboard | A work order has been completed, cancelled, or deferred — closes the observation-to-action loop | Partial status updates mid-execution (not yet supported in v1.3). |
| `asset.hierarchy` | CMMS, ERP, asset register, BIM system | Digital twin, dashboard, graph database | Asset tree structure changes — new equipment, relocation, parent/child relationships | Routine sync of unchanged hierarchy (use idempotent upsert, not repeated events). |
| `sensor.registration` | Edge gateway, IoT platform, device manager | Asset register, provisioning system, monitoring dashboard | A sensor is discovered, registered, calibrated, or decommissioned for the first time or changes state | Every reading cycle. Emit once per state change, not per reading. |
| `maintenance.spare_part_usage` | CMMS, warehouse system, technician app | Inventory system, cost analytics, procurement | Spare parts were consumed during a maintenance action | Generic inventory movements unrelated to maintenance (use your ERP). |

> **Guidance:** `asset.measurement` and `sensor.registration` are high-frequency by nature. Consumers building intelligence dashboards SHOULD filter by `asset.health` and `maintenance.*` event types for actionable signal. Raw measurements belong in time-series storage, not intelligence layers.

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

## Versioning

> **Governance, the compatibility policy, and the change process are normative
> and live in [GOVERNANCE.md](GOVERNANCE.md).** This section summarises how
> versions are numbered; GOVERNANCE.md states what implementers may rely on,
> which changes are compatible, how long a version is supported, and how a
> change is proposed.

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
| 1.1 | March 2026 | 4 new event types (maintenance.completion, asset.hierarchy, sensor.registration, maintenance.spare_part_usage), batch_id envelope field, failure mode taxonomy (Appendix A). |
| 1.2 | March 2026 | ISO alignment: `units_qualifier`, `sampling_rate_hz`, `acquisition_duration_s` on asset.measurement (ISO 17359); `iso_13374_status` on asset.health (ISO 13374); `iso_14224` object on asset.health + maintenance.completion (ISO 14224). All new fields optional — full backward compatibility. Appendix B (ISO 14224 codes), Appendix C (ISO 13374 mapping). |
| 1.3 | March 2026 | State transition model: `condition_trend` field on asset.health (`worsening`, `stable`, `improving`) based on ISO 13374-4 §5.3. Formalized recovery event pattern. State Transition Guidance in Architecture Guide (ISO 13374-4, ISO 17359, ISO 14224, ISO 55000). Recovery event example. All new fields optional — full backward compatibility. |
| 1.4 | September 2026 | **Governance and compatibility policy become normative** ([GOVERNANCE.md](GOVERNANCE.md)): stated stewardship, BACKWARD compatibility as the default mode, a 24-month support window, canonical and resolvable `$id` versioned by URI, and an RFC-based change process. Scope boundaries made explicit: IAES defines no asset hierarchy, no equipment catalog, and no commercial terms. **No schema changed in this release.** **Schema identity corrected** under GOVERNANCE.md §5.1: the eight schemas declared `$id` under `https://iaes.wertek.ai/schema/v1/`, a host that has never resolved (verified 2026-09-03: no DNS answer). They now declare `https://iaes.dev/schema/v1/`, which is served. The old base is permanently reserved and will not be reassigned. Schema content is otherwise unchanged. **New optional envelope field `dataschema`**: the canonical URI of the schema the payload was written against, following the CloudEvents attribute of the same name. Derivable from `event_type`, so both SDKs set it automatically for published event types and omit it otherwise. Optional and additive: fully backward compatible. **`event_type` opened**: it was a closed enumeration of seven values while this same document ordered consumers to tolerate values they do not recognise — a contradiction that made unknown types impossible to produce. It is now a dot-notation pattern with the published types as examples. Widening, therefore backward compatible: every previously valid value still validates, and the compatibility guard verifies that rather than assuming it. |
| 2.0 | September 2026 | **First MAJOR release.** Two things make it major, and only one can affect a producer's existing output. **(1) Timestamps must be RFC 3339**, not merely ISO 8601 — a narrowing, since ordinal dates, week dates and some offset forms are valid ISO 8601 and not valid RFC 3339. No schema enforces it in either direction, because `format` is an annotation in Draft 2020-12, so it will not surface as a validation failure. **(2) The eight schemas publish under `https://iaes.dev/schema/v2/`**, and the envelope constrains `spec_version` to `^2\.[0-9]+$`. The eight `/schema/v1/` URIs continue to resolve, permanently, to the schemas the 1.x line published: a representation served under a major's URI stays that major's and is never regenerated from a later release. A consumer validates an event against the schemas of the major the event declares, which is how a 2.0 consumer reads a 1.4 event. **Wire contract stabilized** (`rfc/IAES-RFC-002.md`): `severity` is not `priority` and neither may be presented as the other; the ISO 13374 attributions on `iso_13374_status` and `condition_trend` are **withdrawn** — the values are IAES's own and the field names are kept for compatibility; an **absent optional field is not an assertion**, so a producer MUST omit rather than substitute and a consumer MUST NOT read absence as a default; `measurement_type` is **open** and any published list is advisory. None of those invalidates a 1.4 event: everything schema-valid under 1.4 stays schema-valid, and a 1.4 producer that keeps substituting stays conforming to 1.4 — it simply cannot declare 2.0. **Governance became testable** (RFC-003 through RFC-007): a criterion for changes to producer and consumer obligations (§4.4), one for changes to the policy itself and the rule that a release takes the maximum level of the changes it carries (§4.5), two classes of conformance with an SDK profile that is claimed and checked rather than granted (§9), and the ratification of everything that had accumulated since 1.4. **Migration:** declare `2.0`, point at `/schema/v2/`, emit RFC 3339 timestamps, take the `2.0.x` packages, and stop substituting values for optional fields the caller did not supply. `from_object` is the canonical constructor name; `from_dict` and `fromJSON` keep working as deprecated aliases. |

## References

What this specification depends on, and how much of that dependency its
machine-validity artifact actually checks. Measured from the artifacts on
2026-09-06.

Two questions, and they are independent:

- **Normative for meaning** — must the value satisfy this document for the
  event to conform to IAES? That is decided by this specification.
- **Enforced by the schema** — does the schema reject a value that does not?
  That is decided by JSON Schema and by what the schemas actually declare.

They are not the same question, and where they disagree the disagreement is
the defect.

| Document | Normative for meaning | Enforced by the schema |
|---|---|---|
| RFC 3339 | **Yes.** `timestamp` MUST be UTC with a timezone designator; `calibration_date` is a date. | **No.** Declared with `format`, which Draft 2020-12 treats as an annotation. |
| RFC 4122 | **Yes** for `event_id`, `correlation_id` and `source_event_id`. | **No.** Same reason. |
| RFC 3986 | **Yes** for `dataschema`, which carries a URI. | **No.** Same reason. |
| RFC 2119, RFC 8174 | **Yes.** How MUST, SHOULD and MAY are to be read here. | **Not applicable.** Not a schema constraint. |
| ISO 4217 | **Yes.** `currency` is an ISO 4217 code. | **Partly.** `^[A-Z]{3}$` checks the shape, not membership: `ZZZ` and `QQQ` pass. |
| ISO 14224 | No. Mentioned for the `iso_14224` object and Appendix B. | No. |
| ISO 17359 | No. Mentioned for `units_qualifier` and the acquisition fields. | No. |
| ISO 13374 series | No. Mentioned for `iso_13374_status`, `condition_trend` and Appendix C. | No. |
| ISO 55000 | No. Mentioned as asset management context. | No. |

### An event can be schema-valid and non-conforming

Broken rather than read, against the validator this repository publishes:

    timestamp      = "banana"          accepted
    event_id       = "no-uuid"         accepted
    correlation_id = "12345"           accepted
    dataschema     = "esto no es uri"  accepted

Each of those satisfies the schema and violates this specification. An
implementer can run the official validator, get green, and produce something
this document forbids. That gap is the finding, not the accepted values.

Switching JSON Schema's format assertion on does not close it. Measured with
the checker enabled, `uuid` is rejected while `date-time` and `uri` are still
accepted, because their checkers live in optional packages — so whether an
event is valid would depend on which packages the reader happens to have
installed, and two conforming readers would disagree about the same bytes.

### Why this is not simply fixed

The schemas already assert `event_type`, `source`, `spec_version` and
`currency` with `pattern`, which every validator applies, while merely
annotating the six identifier and date fields. No document says why the two
groups are treated differently.

Adding a pattern to close the gap is not available inside 1.x:
`GOVERNANCE.md` §4.2 lists *adding a pattern where none existed* as a
narrowing change, therefore MAJOR, and the compatibility guard implements
that. Values that validate today would stop validating.

So this is a decision with real consequences and it belongs in a memo, not in
a references table. This section records the measurement the memo will need.

Three of these documents were unnamed until 2026-09-06. The schemas have
always used `uuid`, `uri`, `date-time` and `date`, so the specification has
always meant to depend on the documents that define them; it named none of
them, and named ISO 8601, which JSON Schema does not use and which the editor
does not hold. An implementer could satisfy the schema and had nowhere to read
why.

The ISO 13374 entries say *series* rather than a part on purpose. The
unqualified citations cover at least two different subjects — health status
levels and a six-block processing model — which cannot both be the same part,
and the editor holds only ISO 13374-4. A citation that does not identify a
document cannot be checked. `rfc/IAES-RFC-002.md` withdrew the ISO 13374 attributions in 2.0; the
field names are retained for compatibility with 1.x, and the values are
declared as IAES's own.

## Appendix A: Failure Mode Taxonomy

Standard failure mode values for use in `asset.health` and `maintenance.completion` events. Based on ISO 14224 failure mode classification. Custom values are allowed — this list provides interoperability defaults.

### Rotating Equipment

| Value | Description |
|-------|-------------|
| `bearing_inner_race` | Inner race defect |
| `bearing_outer_race` | Outer race defect |
| `bearing_ball` | Rolling element defect |
| `bearing_cage` | Cage/retainer defect |
| `misalignment` | Shaft misalignment (angular or parallel) |
| `unbalance` | Mass unbalance |
| `looseness_mechanical` | Mechanical looseness (structural or rotating) |
| `looseness_electrical` | Electrical looseness (connections) |
| `gear_mesh` | Gear mesh defect |
| `gear_tooth` | Gear tooth wear or breakage |

### Electrical

| Value | Description |
|-------|-------------|
| `electrical_fault` | General electrical fault |
| `winding_short` | Stator or rotor winding short circuit |
| `broken_rotor_bar` | Broken rotor bar (induction motors) |
| `eccentricity` | Air gap eccentricity (static or dynamic) |

### Fluid / Thermal

| Value | Description |
|-------|-------------|
| `cavitation` | Cavitation in pumps or valves |
| `overheating` | Abnormal temperature rise |
| `lubrication_failure` | Inadequate or degraded lubrication |
| `seal_leak` | Seal or gasket leak |
| `fouling` | Surface fouling or buildup |
| `corrosion` | Corrosion or material degradation |

Producers SHOULD use these values when applicable. Custom values (e.g. `blade_erosion`, `coupling_wear`) are valid and consumers MUST tolerate them.

## Appendix B: ISO 14224 Failure Classification Codes

Optional structured failure coding for use in the `iso_14224` object on `asset.health` and `maintenance.completion` events. Based on ISO 14224:2016 failure classification.

### Object Structure

```json
{
  "iso_14224": {
    "mechanism_code": "1.1",
    "mechanism_label": "Mechanical wear",
    "cause_code": "4",
    "cause_label": "Operations/Maintenance",
    "detection_method": "2",
    "detection_label": "Condition monitoring"
  }
}
```

All fields are optional. Producers MAY include any subset.

### Failure Mechanism Codes

| Code | Mechanism | Related IAES failure_mode |
|------|-----------|--------------------------|
| 1.1 | Mechanical wear | `bearing_inner_race`, `bearing_outer_race`, `gear_tooth` |
| 1.2 | Fatigue | `bearing_ball`, `bearing_cage` |
| 1.3 | Corrosion | `corrosion` |
| 1.4 | Erosion | `cavitation` |
| 2.1 | Overheating | `overheating` |
| 2.2 | Electrical breakdown | `electrical_fault`, `winding_short` |
| 3.1 | Vibration-induced | `unbalance`, `misalignment`, `looseness_mechanical` |
| 3.2 | Leakage | `seal_leak` |
| 4.1 | Contamination | `fouling`, `lubrication_failure` |

### Failure Cause Codes

| Code | Cause Category |
|------|---------------|
| 1 | Design-related |
| 2 | Fabrication / Manufacturing |
| 3 | Installation |
| 4 | Operations / Maintenance |
| 5 | Management / Organization |
| 6 | Miscellaneous / Unknown |

### Detection Method Codes

| Code | Method | Typical IAES `source` |
|------|--------|-----------------------|
| 1 | Periodic maintenance | `operator.manual_inspection` |
| 2 | Condition monitoring | `vendor.vibration`, `vendor.diagnosis` |
| 3 | Functional testing | `operator.field_assessment` |
| 4 | Casual observation | `operator.manual_inspection` |
| 5 | On demand / Breakdown | — (reactive) |

The `iso_14224` object coexists with the `failure_mode` field from Appendix A. `failure_mode` provides a quick human-readable label; `iso_14224` provides structured classification for interoperability with systems that use ISO 14224 coding (common in oil & gas, power generation, and ISO-certified plants).

## Appendix C: ISO 13374 series Health Status Mapping

The `iso_13374_status` field on `asset.health` carries a health status level from **IAES's own vocabulary**. The attribution to ISO 13374-2 was withdrawn in 2.0: the citation did not identify a part, and the correspondence was never verified against the document. The field name is retained for compatibility with 1.x. It is **complementary** to the IAES `severity` field:

- **`severity`** is ACTION-oriented: what should we DO about this? (info → critical)
- **`iso_13374_status`** is CONDITION-oriented: what IS the current state? (unknown → failed)

### Status Levels

| ISO 13374 series status | Description | Nearest IAES `severity` |
|------------------|-------------|------------------------|
| `unknown` | Insufficient data to determine condition | `info` |
| `normal` | Operating within normal parameters | `info` |
| `satisfactory` | Minor deviations, still acceptable | `low` |
| `unsatisfactory` | Noticeable deviation from normal | `medium` |
| `unacceptable` | Exceeds acceptable operating limits | `high` |
| `imminent_failure` | Failure expected in near term | `critical` |
| `failed` | Asset has failed or is non-functional | `critical` |

### Usage Example

```json
{
  "event_type": "asset.health",
  "data": {
    "health_index": 0.16,
    "severity": "critical",
    "iso_13374_status": "imminent_failure",
    "failure_mode": "bearing_inner_race",
    "rul_days": 5,
    "iso_14224": {
      "mechanism_code": "1.1",
      "mechanism_label": "Mechanical wear",
      "detection_method": "2",
      "detection_label": "Condition monitoring"
    }
  }
}
```

Consumers that understand the ISO 13374 series can use `iso_13374_status` for condition-based reporting. Others use `severity` for action-based alerting. Both fields are optional; when both are present, they provide complementary perspectives.

### ISO 13374 series 6-Block Processing Model

IAES events map to the ISO 13374-2 processing blocks:

| Block | Name | IAES Event |
|-------|------|-----------|
| 1 | Data Acquisition | `asset.measurement` |
| 2 | Data Manipulation | `asset.measurement` (processed values) |
| 3 | State Detection | `asset.health` (anomaly_score) |
| 4 | Health Assessment | `asset.health` (health_index, iso_13374_status) |
| 5 | Prognostic Assessment | `asset.health` (rul_days) |
| 6 | Advisory Generation | `asset.health` (recommended_action) + `maintenance.work_order_intent` |

IAES is an event standard, not a processing pipeline. The 6-block model describes internal processing stages; IAES captures the outputs of those stages as events.

## License

IAES is an open specification licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Implementations may be proprietary.

---

*IAES v2.0 — September 2026*
*Created by the [Wertek AI](https://wertek.ai) team.*
*Implementations are listed in [README.md](README.md). None of them is
privileged: conformance is measured on the wire, not against any one of
them.*
