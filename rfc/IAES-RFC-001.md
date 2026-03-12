```
IAES                                                        G. Garza
Request for Comments: 001                                   Wertek AI
Category: Standards Track                                  March 2026
ISSN: N/A

         Industrial Asset Event Standard (IAES) v1.3
              Industrial Asset Event Model
```

# Status of This Memo

This document specifies an open standard for the industrial asset
intelligence community, and requests discussion and suggestions for
improvements. Distribution of this memo is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI. This document is made available under
the Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

This document defines the Industrial Asset Event Standard (IAES), a
vendor-neutral, transport-agnostic event format specification for
industrial asset intelligence. IAES establishes a common data contract
enabling interoperability between heterogeneous condition monitoring
systems, CMMS platforms, and predictive maintenance pipelines.

The specification defines a unified event envelope and seven event
types covering the full asset monitoring lifecycle: measurement,
health assessment, hierarchy synchronization, sensor registration,
work order intent, maintenance completion, and spare part tracking.

IAES v1.3 aligns with four ISO standards (17359, 13374, 14224, 55000)
and introduces state transition intelligence — a pattern that reduces
continuous telemetry streams into semantic incident lifecycles.

Published SDKs: Python (PyPI), TypeScript (npm), Node-RED (npm).
Schemas and examples: https://iaes.dev

---

# Table of Contents

1. [Introduction](#1-introduction)
2. [Conventions and Definitions](#2-conventions-and-definitions)
3. [Event Envelope](#3-event-envelope)
4. [Event Types](#4-event-types)
5. [ISO Alignment](#5-iso-alignment)
6. [State Transition Intelligence](#6-state-transition-intelligence)
7. [Severity Model](#7-severity-model)
8. [Idempotency and Deduplication](#8-idempotency-and-deduplication)
9. [Security Considerations](#9-security-considerations)
10. [IANA Considerations](#10-iana-considerations)
11. [References](#11-references)
12. [Appendix A: Failure Mode Taxonomy](#appendix-a-failure-mode-taxonomy)
13. [Appendix B: ISO 14224 Codes](#appendix-b-iso-14224-codes)
14. [Appendix C: Version History](#appendix-c-version-history)
15. [Author's Address](#authors-address)

---

# 1. Introduction

## 1.1. Problem Statement

Modern industrial facilities deploy sensors from multiple vendors —
vibration analyzers, power quality meters, thermal cameras, current
transformers — each producing telemetry in proprietary formats. This
fragmentation creates three fundamental problems:

  (a) Correlation blindness: Events from different monitoring systems
      cannot be automatically correlated because they share no common
      event model.

  (b) Intelligence silos: AI models trained on one vendor's data
      format cannot generalize across equipment monitored by different
      vendors without costly ETL pipelines.

  (c) Vendor lock-in: Organizations cannot switch or combine monitoring
      platforms without losing historical event context.

## 1.2. Scope

IAES defines:

  - A common event envelope structure (Section 3)
  - Seven event types for the asset monitoring lifecycle (Section 4)
  - ISO-aligned optional metadata fields (Section 5)
  - A state transition model for incident lifecycles (Section 6)
  - Severity and condition vocabularies (Section 7)
  - Idempotency and deduplication mechanisms (Section 8)

IAES does NOT define:

  - Transport protocols (MQTT, HTTP, Kafka, etc.)
  - Storage formats or database schemas
  - Root cause analysis or diagnostic algorithms
  - Risk scoring or optimization strategies
  - Access control or authentication mechanisms

## 1.3. Design Principles

  P1. Deliberate Incompleteness — IAES carries facts (what, when,
      where, severity). Meaning (why, risk, optimal response) is
      explicitly out of scope.

  P2. Transport Agnosticism — The event structure is valid over MQTT,
      HTTP/REST, Kafka, file transfer, or any future transport.

  P3. Forward Compatibility — Minor versions add optional fields only.
      Consumers built for v1.0 MUST accept events from v1.x.

  P4. ISO Alignment Without Prescription — ISO metadata is optional.
      Consumers that understand ISO semantics benefit; those that do
      not still function correctly.

  P5. Exponential Volume Reduction — Each processing layer reduces
      event volume by orders of magnitude.

  P6. Interoperability by Contract — Producers and consumers agree on
      the data contract; internal implementations are unconstrained.

---

# 2. Conventions and Definitions

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in RFC 2119 [RFC2119].

  **Event** — A discrete, immutable record of something that occurred
  in the context of an industrial asset.

  **Envelope** — The common metadata wrapper shared by all IAES events.

  **Producer** — A system that generates and emits IAES events.

  **Consumer** — A system that receives and processes IAES events.

  **Correlation** — The grouping of causally related events via a
  shared `correlation_id`.

  **Incident** — A sequence of correlated events representing a single
  asset condition episode (onset through recovery).

---

# 3. Event Envelope

## 3.1. Structure

Every IAES event MUST include a common envelope containing metadata
and context. The envelope is serialized as a JSON object.

```json
{
  "spec_version": "1.3",
  "event_type": "asset.health",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
  "source_event_id": "f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
  "batch_id": "sync-2026-03-11-001",
  "timestamp": "2026-03-11T14:30:00Z",
  "source": "wertek.ai.vibration",
  "content_hash": "a1b2c3d4e5f6a7b8",
  "asset": {
    "asset_id": "PUMP-001",
    "asset_name": "Cooling Water Pump #1",
    "plant": "Pesqueria",
    "area": "Turbine Hall"
  },
  "data": { }
}
```

## 3.2. Field Definitions

### 3.2.1. spec_version (REQUIRED)

  Type: string
  Format: Semantic version (major.minor)
  Example: "1.3"

  The IAES specification version. Consumers MUST validate the major
  version and SHOULD tolerate unknown minor versions.

### 3.2.2. event_type (REQUIRED)

  Type: string
  Format: Dot-notation namespace
  Values: See Section 4

  Classifies the event. Consumers MUST tolerate unknown event types
  by ignoring events they cannot process.

### 3.2.3. event_id (REQUIRED)

  Type: string
  Format: UUID v4

  Globally unique identifier. MUST NOT be reused. Producers MUST
  generate a new UUID for each event.

### 3.2.4. correlation_id (OPTIONAL)

  Type: string
  Format: UUID v4

  Groups causally related events. All events in an incident lifecycle
  (onset, escalation, recovery) SHOULD share the same correlation_id.

### 3.2.5. source_event_id (OPTIONAL)

  Type: string | null
  Format: UUID v4

  References the event_id of the causally preceding event. Enables
  construction of directed event graphs for traceability.

### 3.2.6. batch_id (OPTIONAL)

  Type: string | null

  Groups events from a single bulk operation (e.g., gateway poll,
  hierarchy sync). Added in v1.1.

### 3.2.7. timestamp (REQUIRED)

  Type: string
  Format: ISO 8601 UTC (YYYY-MM-DDTHH:MM:SSZ)

  The time at which the event occurred. Producers MUST use UTC.

### 3.2.8. source (REQUIRED)

  Type: string
  Format: Dot-notation (vendor.system[.subsystem])
  Examples: "wertek.ai.vibration", "operator.manual_inspection"

  Identifies the producing system. Consumers MAY use source for
  routing, filtering, or trust decisions.

### 3.2.9. content_hash (OPTIONAL)

  Type: string
  Format: First 16 characters of SHA-256

  Computed as: `sha256(json_dumps(data, sort_keys=True))[:16]`

  Enables deduplication without full payload comparison. See Section 8.

### 3.2.10. asset (REQUIRED)

  Type: object

  | Field      | Required | Type   | Description              |
  |------------|----------|--------|--------------------------|
  | asset_id   | Yes      | string | Unique asset identifier  |
  | asset_name | No       | string | Human-readable name      |
  | plant      | No       | string | Plant or facility name   |
  | area       | No       | string | Area within plant        |

### 3.2.11. data (REQUIRED)

  Type: object

  Event-specific payload. Structure defined per event_type in
  Section 4. Consumers MUST tolerate unknown fields within data.

---

# 4. Event Types

IAES v1.3 defines seven event types in three categories.

| Event Type                       | Category    | Since |
|----------------------------------|-------------|-------|
| `asset.measurement`              | Telemetry   | v1.0  |
| `asset.health`                   | Intelligence| v1.0  |
| `asset.hierarchy`                | Structure   | v1.1  |
| `sensor.registration`            | Structure   | v1.1  |
| `maintenance.work_order_intent`  | Action      | v1.0  |
| `maintenance.completion`         | Feedback    | v1.1  |
| `maintenance.spare_part_usage`   | Feedback    | v1.1  |

## 4.1. asset.measurement

Physical sensor reading from an asset.

### Required Fields

| Field            | Type   | Description                        |
|------------------|--------|------------------------------------|
| measurement_type | string | Type: vibration_velocity, temperature, current, power_factor, thd_voltage, etc. |
| value            | number | Numeric reading                    |
| unit             | string | Engineering unit (mm/s, C, A, %, Hz) |

### Optional Fields (v1.2 — ISO 17359)

| Field                | Type   | Description                              |
|----------------------|--------|------------------------------------------|
| units_qualifier      | string | Signal processing: rms, peak, peak_to_peak, average, true_rms |
| sampling_rate_hz     | number | Sampling rate of acquisition             |
| acquisition_duration_s | number | Length of measurement window            |

The `units_qualifier` field resolves a critical ambiguity: a vibration
reading of "4.5 mm/s" is meaningless without knowing whether it
represents RMS, peak, or peak-to-peak — each implies different
severity thresholds per ISO 10816.

## 4.2. asset.health

AI diagnosis, rule-engine evaluation, or expert assessment.

### Required Fields

| Field        | Type        | Description                        |
|--------------|-------------|------------------------------------|
| health_index | float [0,1] | Normalized health (0=failed, 1=healthy) |
| severity     | enum        | info, low, medium, high, critical  |

### Optional Fields

| Field                   | Type        | Since | Description                    |
|-------------------------|-------------|-------|--------------------------------|
| anomaly_score           | float [0,1] | v1.0  | Probability of anomaly         |
| failure_mode            | string      | v1.0  | Classified fault (Appendix A)  |
| fault_confidence        | float [0,1] | v1.0  | Classification confidence      |
| rul_days                | integer     | v1.0  | Remaining useful life (days)   |
| recommended_action      | string      | v1.0  | Human-readable recommendation  |
| estimated_downtime_hours| float       | v1.0  | Repair duration estimate       |
| iso_13374_status        | enum        | v1.2  | ISO condition state (Sec. 5.2) |
| iso_14224               | object      | v1.2  | Failure classification (Sec. 5.4) |
| condition_trend         | enum        | v1.3  | worsening, stable, improving   |

### Severity vs. iso_13374_status

These fields are COMPLEMENTARY, not redundant:

  - `severity` is ACTION-oriented: "what should we do?"
  - `iso_13374_status` is CONDITION-oriented: "what IS the state?"

A motor bearing may have `severity: "low"` (no urgent action) with
`iso_13374_status: "satisfactory"` (minor deviation detected).

## 4.3. maintenance.work_order_intent

Declaration of intent to create a work order.

### Required Fields

| Field    | Type   | Description                            |
|----------|--------|----------------------------------------|
| title    | string | Work order title                       |
| priority | enum   | low, medium, high, emergency           |

### Optional Fields

| Field               | Type    | Description                         |
|---------------------|---------|-------------------------------------|
| description         | string  | Detailed rationale                  |
| recommended_due_days| integer | Suggested deadline                  |
| triggered_by        | string  | alert, schedule, manual, threshold, ai_diagnosis |

The producer SUGGESTS; the consumer DECIDES. This semantic prevents
alert storms by decoupling detection from action.

## 4.4. maintenance.completion

Acknowledges completion of a work order. The only event type that
flows "backward" (CMMS -> monitoring platform).

### Required Fields

| Field         | Type   | Description                            |
|---------------|--------|----------------------------------------|
| status        | enum   | completed, partially_completed, cancelled, deferred |
| work_order_id | string | ID of the completed order              |

### Optional Fields

| Field                  | Type    | Description                       |
|------------------------|---------|-----------------------------------|
| actual_duration_seconds| integer | Time spent on work                |
| technician_id          | string  | Opaque technician identifier      |
| failure_confirmed      | boolean | Was the predicted fault real?     |
| failure_mode           | string  | Confirmed failure mode            |
| spare_parts_count      | integer | Parts consumed (summary)          |
| iso_14224              | object  | Confirmed failure classification  |

The `failure_confirmed` boolean is CRITICAL for ML feedback loops,
enabling measurement of prediction accuracy.

## 4.5. asset.hierarchy

Synchronizes asset hierarchy across systems.

### Required Fields

| Field             | Type   | Description                          |
|-------------------|--------|--------------------------------------|
| hierarchy_level   | enum   | organization, plant, area, equipment |
| relationship_type | enum   | parent_of, child_of, sibling_of, depends_on |

Multiple events with the same `correlation_id` + `batch_id`
represent a complete hierarchy synchronization.

## 4.6. sensor.registration

Sensor discovery, onboarding, and lifecycle tracking.

### Required Fields

| Field               | Type   | Description                        |
|---------------------|--------|------------------------------------|
| sensor_id           | string | Unique sensor identifier           |
| registration_status | enum   | discovered, registered, calibrated, decommissioned |

### Optional Fields

| Field                    | Type   | Description                     |
|--------------------------|--------|---------------------------------|
| measurement_capabilities | array  | What this sensor measures       |
| communication_protocol   | string | mqtt, modbus_tcp, opcua, lorawan|
| calibration_date         | string | Last calibration (ISO 8601)     |

## 4.7. maintenance.spare_part_usage

Records spare parts consumed during maintenance.

### Required Fields

| Field         | Type   | Description                          |
|---------------|--------|--------------------------------------|
| work_order_id | string | Associated work order                |
| spare_part_id | string | Part identifier in inventory system  |
| quantity_used | number | Quantity consumed                    |

### Optional Fields

| Field       | Type   | Description            |
|-------------|--------|------------------------|
| part_number | string | Manufacturer part number |
| unit_cost   | number | Cost per unit          |
| currency    | string | ISO 4217 currency code |
| total_cost  | number | Total cost             |

---

# 5. ISO Alignment

IAES operationalizes four ISO standards without mandating compliance.
All ISO fields are OPTIONAL — enrichment without breaking backward
compatibility.

## 5.1. ISO 17359: Condition Monitoring Guidelines

IAES v1.2 implements three ISO 17359 requirements in
`asset.measurement`:

  1. `units_qualifier` — Signal processing method (ISO 17359 Section 6.3)
  2. `sampling_rate_hz` — Acquisition frequency (Nyquist compliance)
  3. `acquisition_duration_s` — Measurement window length

## 5.2. ISO 13374: Open System Architecture

ISO 13374 defines a six-block processing model. IAES maps as follows:

| Block | Function            | IAES Mapping                      |
|-------|---------------------|-----------------------------------|
| 1     | Data Acquisition    | `asset.measurement`               |
| 2     | Data Manipulation   | `asset.measurement` (processed)   |
| 3     | State Detection     | `asset.health.anomaly_score`      |
| 4     | Health Assessment   | `asset.health.health_index`       |
| 5     | Prognosis           | `asset.health.rul_days`           |
| 6     | Advisory            | `maintenance.work_order_intent`   |

IAES collapses blocks 3-5 into a single `asset.health` event. The
standard captures OUTPUTS of processing stages, not the stages.

The `iso_13374_status` vocabulary:

  unknown | normal | satisfactory | unsatisfactory |
  unacceptable | imminent_failure | failed

## 5.3. ISO 13374-4: Condition Trend

ISO 13374-4 Section 5.3 distinguishes "serious but stable" from
"serious and worsening." IAES v1.3 implements this via:

  `condition_trend`: worsening | stable | improving

## 5.4. ISO 14224: Failure Classification

The `iso_14224` object carries structured failure data:

```json
{
  "failure_mechanism": "1.1",
  "failure_cause": "operations",
  "detection_method": "condition_monitoring",
  "equipment_class": "pump_centrifugal"
}
```

---

# 6. State Transition Intelligence

## 6.1. The Alert Storm Problem

A sensor sampling at 1 Hz that exceeds a threshold continuously
produces 86,400 alerts per day for a single persistent fault. IAES
solves this by emitting events only at state transitions.

## 6.2. Incident Lifecycle State Machine

```
                  violation          severity UP
  ┌────────┐    ──────────>    ┌───────┐    ──────────>    ┌──────────┐
  │ NORMAL │                   │ ONSET │                   │ ESCALATE │
  └────────┘                   └───────┘                   └──────────┘
       ^                          │  ^                          │
       │                     n OK │  │ relapse              n OK│
       │          confirmed       v  │                          v
       │                       ┌─────────┐                      │
       └────────────────────── │ RECOVER │ <────────────────────┘
                               └─────────┘
```

  **Onset:** First violation for (asset_id, rule_key). Generates new
  `correlation_id`. Emits `asset.health` with
  `condition_trend: "worsening"`.

  **Escalation:** Same incident, severity increases. Same
  `correlation_id`, `source_event_id` links to onset.

  **Recovery:** n consecutive OK readings after violation. Same
  `correlation_id`. Emits `condition_trend: "improving"`,
  `severity: "info"`, `iso_13374_status: "normal"`.

Transitions emit events. Steady states are SILENT.

## 6.3. Hysteresis Parameters

  recovery_count (n = 5):
    Minimum consecutive OK readings required.

  recovery_margin_pct (m = 2.0%):
    Value must clear threshold by margin.

  min_incident_duration_s (d = 120s):
    Minimum incident duration before recovery.

Recovery condition:

  recover <=> for all i in [1,n]: v_i < threshold * (1 - m)
              AND t_now - t_onset > d

## 6.4. Dimensionality Reduction

| Approach                      | Events | Reduction       |
|-------------------------------|--------|-----------------|
| Traditional (per-reading)     | 28,800 | —               |
| IAES state transitions        | 2–4    | 7,200–14,400x   |

For a persistent fault lasting 8 hours on a 1 Hz sensor.

## 6.5. ML Feature Extraction

| Feature                  | Derivation                          |
|--------------------------|-------------------------------------|
| Incident duration        | t_recovery - t_onset                |
| Escalation rate          | delta_severity / delta_t            |
| Escalation count         | Count of escalation events          |
| Time to first escalation | t_escalation_1 - t_onset            |
| Recovery confirmation    | failure_confirmed in completion     |

---

# 7. Severity Model

## 7.1. Five-Level Hierarchy

| Level    | Meaning   | Action Required       | ISO Zone       |
|----------|-----------|-----------------------|----------------|
| info     | Normal    | None                  | A (Good)       |
| low      | Minor     | Monitor, trend        | B (Acceptable) |
| medium   | Moderate  | Plan intervention     | B upper        |
| high     | Significant| Schedule within days | C (Alarm)      |
| critical | Immediate | Immediate response    | D (Danger)     |

## 7.2. External System Mapping

| IAES     | SAP PM Prio | MaintainX | Odoo Priority    |
|----------|-------------|-----------|------------------|
| info     | —           | —         | —                |
| low      | Priority 4  | LOW       | 0 (Very Urgent: No) |
| medium   | Priority 3  | MEDIUM    | 1 (Normal)       |
| high     | Priority 2  | HIGH      | 2 (Urgent)       |
| critical | Priority 1  | HIGH      | 3 (Very Urgent)  |

---

# 8. Idempotency and Deduplication

## 8.1. Three Deduplication Mechanisms

  1. **event_id** — UUID v4, globally unique, never reused. Handles
     exact retransmissions.

  2. **content_hash** — SHA-256 prefix (16 chars) of sorted JSON data.
     Catches semantic duplicates with different event_ids.

  3. **Composite key** — (content_hash, asset_id, event_type).
     RECOMMENDED deduplication key for consumers.

## 8.2. Producer Rules

  Producers MUST:
  - Set all REQUIRED envelope fields
  - Generate unique event_id (UUID v4) per event
  - Use dot-notation for source
  - Use ISO 8601 UTC for timestamp
  - NOT assume consumer behavior

  Producers SHOULD:
  - Use correlation_id to group related events
  - Use source_event_id for causal chains
  - Compute content_hash for deduplication

## 8.3. Consumer Rules

  Consumers MUST:
  - Tolerate unknown fields in data
  - Tolerate unknown event_type values
  - Validate spec_version major version

  Consumers SHOULD:
  - Deduplicate on (content_hash, asset_id, event_type)
  - Use correlation_id to group and order events
  - Map severity to native priority per Section 7.2

---

# 9. Security Considerations

## 9.1. Transport Encryption

  - MQTT: TLS 1.3 RECOMMENDED
  - HTTP/REST: HTTPS with TLS 1.3 REQUIRED
  - Files: GPG or AES-256 encryption RECOMMENDED

## 9.2. Authentication

  - Edge devices: mTLS certificates
  - Cloud-to-cloud: API keys scoped per organization
  - SaaS integrations: OAuth 2.0
  - Webhooks: HMAC signatures (X-IAES-Signature: sha256=<hmac>)

## 9.3. Data Isolation

  Every event includes organization context (implicit or explicit).
  Consumers MUST enforce organization-level isolation.

## 9.4. Privacy by Design

  IAES events contain NO personally identifiable information (PII):
  - technician_id is an opaque identifier (not name/email)
  - asset_id references equipment (not personnel)
  - Location refers to asset location (not personnel tracking)

  IAES events MAY be transmitted, stored, and analyzed without GDPR
  or similar data protection obligations.

---

# 10. IANA Considerations

This document has no IANA actions. IAES event types are managed by
the IAES specification maintainers at https://iaes.dev.

---

# 11. References

## 11.1. Normative References

  [RFC2119]  Bradner, S., "Key words for use in RFCs to Indicate
             Requirement Levels", BCP 14, RFC 2119, March 1997.

## 11.2. Informative References

  [ISO17359] ISO 17359:2018, "Condition monitoring and diagnostics of
             machines — General guidelines", 2018.

  [ISO13374] ISO 13374-1:2003, "Condition monitoring and diagnostics
             of machines — Data processing, communication and
             presentation — Part 1: General guidelines", 2003.

  [ISO14224] ISO 14224:2016, "Petroleum, petrochemical and natural gas
             industries — Collection and exchange of reliability and
             maintenance data for equipment", 2016.

  [ISO10816] ISO 10816-3:2009, "Mechanical vibration — Evaluation of
             machine vibration by measurements on non-rotating parts",
             2009.

  [ISO55000] ISO 55000:2014, "Asset management — Overview, principles
             and terminology", 2014.

  [OPCUA]    OPC Foundation, "OPC Unified Architecture Specification",
             Parts 1-14, Release 1.04, 2017.

  [SPARKPLUG] Eclipse Foundation, "Sparkplug Specification",
              Version 3.0.0, 2022.

  [MOBLEY]   Mobley, R.K., "An Introduction to Predictive
             Maintenance", 2nd ed., Butterworth-Heinemann, 2002.

  [BRANSBY]  Bransby, M.L. and Jenkinson, J., "The management of
             alarm systems", HSE Contract Research Report No. 166,
             1998.

  [JARDINE]  Jardine, A.K.S., Lin, D., and Banjevic, D., "A review
             on machinery diagnostics and prognostics implementing
             condition-based maintenance", Mechanical Systems and
             Signal Processing, vol. 20, no. 7, pp. 1483-1510, 2006.

---

# Appendix A: Failure Mode Taxonomy

Standard failure mode identifiers (non-exhaustive). Custom values
are permitted.

## A.1. Rotating Equipment

| Identifier            | Description           |
|-----------------------|-----------------------|
| bearing_inner_race    | Inner race defect     |
| bearing_outer_race    | Outer race defect     |
| bearing_ball          | Ball/roller defect    |
| bearing_cage          | Cage defect           |
| misalignment          | Shaft misalignment    |
| unbalance             | Rotating unbalance    |
| looseness_mechanical  | Mechanical looseness  |
| looseness_electrical  | Electrical looseness  |
| gear_mesh             | Gear mesh anomaly     |
| gear_tooth            | Gear tooth defect     |

## A.2. Electrical

| Identifier            | Description           |
|-----------------------|-----------------------|
| electrical_fault      | General electrical    |
| winding_short         | Stator winding short  |
| broken_rotor_bar      | Rotor bar defect      |
| eccentricity          | Air gap eccentricity  |

## A.3. Fluid / Thermal

| Identifier            | Description           |
|-----------------------|-----------------------|
| cavitation            | Pump cavitation       |
| overheating           | Thermal anomaly       |
| lubrication_failure   | Lubrication issue     |
| seal_leak             | Seal leakage          |
| fouling               | Surface fouling       |
| corrosion             | Corrosion damage      |

---

# Appendix B: ISO 14224 Codes

## B.1. Failure Mechanisms

| Code | Description           |
|------|-----------------------|
| 1.1  | Mechanical wear       |
| 1.2  | Fatigue               |
| 2.1  | Overheating           |
| 2.2  | Electrical short      |
| 3.1  | Corrosion external    |
| 3.2  | Corrosion internal    |

## B.2. Failure Causes

  design | fabrication | installation | operations | management

## B.3. Detection Methods

  periodic_maintenance | condition_monitoring |
  functional_testing | casual_observation

---

# Appendix C: Version History

| Version | Date       | Changes                                          |
|---------|------------|--------------------------------------------------|
| 1.0     | 2026-03-01 | Initial: 3 event types, envelope                 |
| 1.1     | 2026-03-05 | 4 new event types, batch_id, failure taxonomy     |
| 1.2     | 2026-03-08 | ISO alignment: units_qualifier, iso_13374_status, iso_14224 |
| 1.3     | 2026-03-11 | State transitions: condition_trend, recovery events |

All minor versions are backward compatible. Consumers built for
v1.0 SHOULD accept events from any v1.x without error.

---

# Author's Address

```
Gilberto Garza Gonzalez
Wertek AI
Monterrey, Nuevo Leon, Mexico

Email: gilberto@wertek.ai
URI:   https://iaes.dev
```
