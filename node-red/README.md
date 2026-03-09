# node-red-contrib-iaes

> IAES Industrial Asset Event Standard nodes for Node-RED.

Create, validate, and route vendor-neutral industrial asset events — no code required.

## Install

In your Node-RED directory:

```bash
npm install node-red-contrib-iaes
```

Or via the Node-RED palette manager: search for `node-red-contrib-iaes`.

## Nodes

| Node | Purpose |
|------|---------|
| **iaes measurement** | Create `asset.measurement` events (vibration, temperature, pressure, power factor, THD...) |
| **iaes health** | Create `asset.health` events (AI diagnosis, health index, fault classification, RUL) |
| **iaes work order** | Create `maintenance.work_order_intent` events |
| **iaes validate** | Validate any IAES event against the JSON schema |

## Usage

### Sensor to IAES measurement

```
[inject] --> [iaes measurement] --> [mqtt out]
```

Configure the **iaes measurement** node with asset_id, measurement_type, and unit. The node reads `msg.payload` as the value and outputs a complete IAES envelope.

### Dynamic values from msg

All nodes accept values from `msg` properties. Leave a field empty in the config and set it via `msg`:

- `msg.payload` — the measurement value (number)
- `msg.asset_id` — override asset ID
- `msg.source` — override source identifier
- `msg.measurement_type` — override measurement type
- `msg.unit` — override unit

### Validate incoming events

```
[mqtt in] --> [iaes validate] --> [function]
                |
                +--> [debug] (invalid events)
```

The **iaes validate** node has two outputs: valid events on output 1, invalid events on output 2.

## Examples

### Vibration monitoring

```
[Modbus read] --> [function: extract value] --> [iaes measurement] --> [mqtt out]
```

### Power quality (ION 8650)

```
[Modbus TCP] --> [iaes measurement (power_factor)] --> [mqtt out]
[Modbus TCP] --> [iaes measurement (thd_voltage)]  --> [mqtt out]
```

### AI health diagnosis pipeline

```
[mqtt in] --> [iaes validate] --> [function: run model] --> [iaes health] --> [mqtt out]
```

## Links

- [IAES Specification](https://iaes.dev)
- [Python SDK](https://pypi.org/project/iaes/) — `pip install iaes`
- [TypeScript SDK](https://www.npmjs.com/package/@iaes/sdk) — `npm install @iaes/sdk`
- [GitHub](https://github.com/wertek-ai/iaes)
