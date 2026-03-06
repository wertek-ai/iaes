# IAES — Industrial Asset Event Standard

> A vendor-neutral event specification for industrial asset measurements, diagnoses, and maintenance intents.

IAES defines how industrial observations — whether from sensors, AI engines, or human experts — are represented and transferred across operational systems like CMMS, historians, SCADA platforms, and dashboards.

## Why IAES?

Industrial systems speak different languages. A vibration sensor outputs raw waveforms. An AI model outputs health scores. SAP expects maintenance notifications. PI System expects tag values. MaintainX expects user variables.

IAES provides the **neutral layer in between** — a common event format that any producer can emit and any consumer can understand, without knowing each other's implementation.

```
Signals ──> Intelligence ──> IAES Standard ──> Connectors ──> Enterprise Systems
```

## Event Types (v1.0)

| Event Type | Purpose |
|------------|---------|
| `asset.measurement` | Physical sensor reading (vibration, temperature, pressure, current, etc.) |
| `asset.health` | AI diagnosis or expert assessment (health index, fault classification, RUL, recommended action) |
| `maintenance.work_order_intent` | Intent to create a work order (the consumer decides how to act) |

## Quick Example

```json
{
  "spec_version": "1.0",
  "event_type": "asset.health",
  "event_id": "a9e3c4b2-9d3a-4a12-b1f3-2e44a1caa8a1",
  "correlation_id": "3b2f9d8c-1c33-4a8a-9b77-54d11b2efc12",
  "timestamp": "2026-03-06T17:50:17Z",
  "source": "wertek.ai.vibration",
  "content_hash": "8a3f9c2e1b4d7e6f",
  "asset": {
    "asset_id": "MOTOR-001",
    "asset_name": "Motor Bomba P-101",
    "plant": "Pesqueria",
    "area": "Turbinas"
  },
  "data": {
    "health_index": 0.16,
    "anomaly_score": 0.92,
    "severity": "critical",
    "failure_mode": "bearing_inner_race",
    "rul_days": 5,
    "recommended_action": "Replace bearing immediately"
  }
}
```

## Website

**[iaes.dev](https://iaes.dev)** — Browse the specification, schemas, and examples online.

## Specification

- **[IAES_SPEC.md](IAES_SPEC.md)** — Full specification (human-readable)
- **[schema/](schema/)** — JSON Schema files (machine-readable)
  - `iaes-envelope.schema.json` — Common envelope
  - `asset-measurement.schema.json`
  - `asset-health.schema.json`
  - `maintenance-work-order-intent.schema.json`
- **[examples/](examples/)** — Complete JSON examples
  - `asset-health-ai.json` — AI-originated health event
  - `asset-health-human.json` — Human expert assessment
  - `asset-measurement.json` — Sensor reading
  - `work-order-intent.json` — Work order intent
  - `full-flow.json` — Complete flow (measurement -> diagnosis -> intent)

## Design Principles

1. **Vendor neutrality** — No dependency on any specific system
2. **Legacy compatibility** — Maps cleanly to CMMS, historians, SCADA, IoT
3. **Event-oriented** — Each object represents something that happened
4. **Complete traceability** — `event_id` + `correlation_id` + `source_event_id`
5. **Extensibility** — `data` payload allows new fields without breaking consumers

## Producers

IAES events are produced by systems capable of **interpreting** operational signals — not by the signals themselves. A PLC knows `vibration_rms = 4.6`. That is telemetry. IAES begins where interpretation begins.

| Producer | `source` example |
|----------|-----------------|
| AI diagnosis engine | `wertek.ai.vibration` |
| Rule / threshold engine | `acme.rule_engine` |
| Manual inspection | `operator.manual_inspection` |
| Expert assessment | `operator.field_assessment` |
| Lab analysis | `lab.oil_analysis` |
| Maintenance application | `wertek.ai.cmms` |

Operational systems (PLCs, SCADA, sensor gateways) emit raw signals. These are converted into IAES events by downstream intelligence layers. An edge device MAY produce IAES directly if it has sufficient intelligence (edge AI, embedded rule engine).

## System Compatibility

| System | IAES Mapping |
|--------|-------------|
| SAP PM | Maintenance Notification / Order |
| PI System | Tag value writes |
| AVEVA Data Hub | SDS Stream writes |
| Odoo | maintenance.request |
| MaintainX | User Variables |
| Fracttal | Custom fields + OT |

## Roadmap

**v1.1** (planned):
- `asset.hierarchy` — Asset tree sync
- `sensor.registration` — Sensor onboarding
- `maintenance.completion` — WO completion acknowledgment
- `maintenance.spare_part_usage` — Parts consumed

## Reference Implementation

The reference implementation is the [Wertek AI Integration Framework](https://wertek.ai), which uses IAES internally for all connector adapters.

## License

IAES is an open specification. The specification text and JSON schemas are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Implementations may be proprietary.

---

*IAES v1.0 — March 2026*
