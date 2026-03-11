<p align="center">
  <a href="https://iaes.dev">
    <img src="../assets/iaes-logo.svg" alt="IAES" width="64" height="64">
  </a>
</p>

# n8n-nodes-iaes

IAES Industrial Asset Event Standard nodes for [n8n](https://n8n.io) — emit, validate, and track lifecycle of industrial asset events.

## Nodes

### IAES Emit

Create any IAES v1.3 event type with a visual form:

- **Asset Health** — AI diagnosis, severity, condition trend, ISO 13374 status
- **Asset Measurement** — sensor readings (vibration, temperature, current, etc.)
- **Work Order Intent** — maintenance work order creation intent
- **Maintenance Completion** — work order completion acknowledgment
- **Sensor Registration** — sensor discovery and lifecycle
- **Spare Part Usage** — parts consumed during maintenance

### IAES Validate

Validate incoming JSON against the IAES spec. Two outputs:

- **Valid** — events that pass envelope + schema validation
- **Invalid** — events that fail, with detailed error messages

Supports strict mode for event-type-specific field validation.

### IAES Lifecycle

Incident state machine that tracks onset → escalation → recovery:

- **Output 1 (Onset/Escalation)** — new incidents or severity increases
- **Output 2 (Recovery)** — incident resolved after N consecutive OK readings
- **Output 3 (Suppressed)** — same-severity readings (optional output)

Uses `correlation_id` for incident tracking. State persists across executions via n8n workflow static data.

## Installation

In n8n, go to **Settings → Community Nodes** and install:

```
n8n-nodes-iaes
```

Or via npm:

```bash
npm install n8n-nodes-iaes
```

## Credentials

Configure **IAES API** credentials with:

- **HTTP** — endpoint URL + API key (for REST ingest)
- **MQTT** — broker URL + credentials (for MQTT publish)

## Example Workflows

### PLC → MQTT → n8n → IAES (Quickstart)

Most integrators start here: **"Where does my PLC fit?"**

```
┌─────────┐  MQTT   ┌──────────────┐        ┌───────────┐        ┌──────────┐
│  PLC /  │───────→│ MQTT Trigger │──────→│ IAES Emit │──────→│ HTTP Req │
│  SCADA  │ topic:  │ (n8n built-in)│  JSON  │ (this pkg)│  POST  │ your API │
└─────────┘ plc/    └──────────────┘        └───────────┘        └──────────┘
            data
```

Your PLC publishes raw readings to an MQTT topic. n8n picks them up and wraps them in a standards-compliant IAES envelope:

```
MQTT topic: site-01/plc/compressor-04/vibration
Payload:    { "value": 4.2, "unit": "mm/s" }
```

In the **IAES Emit** node, map the PLC fields:

| IAES Emit Field | n8n Expression |
|-----------------|----------------|
| Event Type | `asset.measurement` |
| Asset ID | `={{ $json.topic.split('/')[2] }}` — e.g. `compressor-04` |
| Source | `plc.site-01` |
| Measurement Type | `vibration_velocity` |
| Value | `={{ $json.message.value }}` — e.g. `4.2` |
| Unit | `={{ $json.message.unit }}` — e.g. `mm/s` |

The output is a full IAES v1.3 envelope ready to POST to any CMMS, data lake, or Wertek.

> **Works with:** Allen-Bradley, Siemens S7 (via MQTT gateway), Modbus TCP (via Node-RED bridge), OPC-UA publishers, any device that can write to MQTT.

### Predictive Maintenance Pipeline

```
Webhook → IAES Validate → IAES Lifecycle → IF Onset → IAES Emit (Work Order Intent)
```

### Energy Anomaly Detection

```
Schedule → HTTP Request (meter API) → IAES Emit (Health) → IAES Lifecycle → Slack Alert
```

### Multi-CMMS Fan-out

```
MQTT Trigger → IAES Validate → IAES Lifecycle → Switch (severity)
  → high/critical: SAP PM + Email
  → medium: MaintainX
  → low: Log only
```

## Links

- [IAES Spec](https://iaes.dev)
- [Python SDK](https://pypi.org/project/iaes/)
- [TypeScript SDK](https://www.npmjs.com/package/@iaes/sdk)
- [Node-RED nodes](https://www.npmjs.com/package/node-red-contrib-iaes)

## License

CC-BY-4.0
