# Changelog

All three IAES packages are versioned together when a change crosses them.

- `node-red-contrib-iaes` (npm) — the Node-RED palette
- `@iaes/sdk` (npm) — TypeScript SDK
- `iaes` (PyPI) — Python SDK

---

## 2026-08-14

### The ingest route was wrong in all three SDKs

Every client published to `{base}/api/v1/iaes/ingest`. IAES servers mount the
route at the root: **`/iaes/ingest`**. The `/api/v1` prefix came from stale
docstrings and had never been checked against a running server, so *every*
publish attempt returned **404** — from the Node-RED node, the TypeScript SDK
and the Python SDK alike.

The Node-RED node had a second, independent defect: it sent the key as
`Authorization: Bearer`, while the ingest authenticates with **`X-API-Key`**.
Even against the correct path it would have returned **401**.

Fixed in `node-red/nodes/iaes-publish.js`, `npm/src/client.ts` and
`src/iaes/client.py`. Both the path and the auth header are now configurable,
with the correct values as defaults.

> **Publish order:** `@iaes/sdk@0.3.0` first, then `node-red-contrib-iaes@0.4.0`,
> which depends on it.

---

## node-red-contrib-iaes 0.4.0

### Fixed

- **`iaes-publish` could not reach any IAES server** — see above. Path and auth
  header are now settings; defaults are `/iaes/ingest` and `X-API-Key`.
- **`iaes-sparkplug` mislabelled namespaced metrics, silently.** Type inference
  scanned for substrings in map-declaration order, so a general key won over a
  specific one. Real gateway tags are namespaced, which meant the broken path
  was the *normal* path:

  | Metric | Before | Now |
  |---|---|---|
  | `Motor1_Vibration_Acceleration` | `vibration_velocity` (mm/s) | `vibration_acceleration` (g) |
  | `Motor_Power_Factor` | `power` (kW) | `power_factor` (ratio) |
  | `Panel_THD_Current` | `current` (A) | `thd_current` (%) |
  | `Pump_Reactive_Power` | `power` (kW) | `reactive_power` (kVAR) |

  Matching now walks contiguous **token windows**, widest first — deterministic
  regardless of map order, and it cannot match across a word boundary.
- **`iaes-health` turned a health index of `0` into `1.0`.** The configured
  default went through `parseFloat(x) || 1.0`, so the worst possible condition
  was published as a perfectly healthy asset. Same fix applied to
  `anomaly_score`, `fault_confidence` and `rul_days`.
- **`iaes-publish` dropped buffered events on redeploy.** The close handler
  cleared the buffer without flushing it and without completing the pending
  messages. It now flushes first.
- **`iaes-validate` did not validate.** It checked three fields while its
  documentation promised validation against the JSON schema; an event with no
  `timestamp`, no `event_id` and a malformed `source` passed as valid. It now
  checks every required envelope field, the `spec_version` and `source`
  patterns, UUID formats, `content_hash` length, and the required `data` fields
  for each of the 7 event types — reporting **all** problems in
  `msg.iaes_errors`, not just the first.
- **`iaes-sparkplug` masked protobuf decode errors.** A corrupt payload fell
  through to `JSON.parse` and surfaced as "Unexpected token", pointing at the
  wrong problem. The decoder is now resolved before decoding.
- Sparkplug default unit for temperature is `C`, matching the IAES schemas
  (was `°C`).

### Added

- `iaes-publish` recognises **cadence backpressure**. A server may refuse events
  arriving faster than the asset's registered interval, answering
  `{"status":"dropped","reason":"cadence_gate"}`. That is not a failure: the
  node reports it in yellow and exposes `cadence_dropped` instead of a generic
  HTTP error. Enforcement stays on the server — the node never sets its own
  rate limit.
- `iaes-publish` caps Batch Size at **100**, the server-side batch limit. Above
  it the whole batch was rejected with 422.
- `iaes-route` sets `msg.iaes_unknown_event_type` on output 7, which otherwise
  cannot be told apart from a valid `maintenance.spare_part_usage`.
- Output messages from `iaes-publish` preserve the original `msg` (`_msgid`,
  `topic`, …) instead of being replaced by a bare payload.

### Tests

- 23 → **77 tests, all passing.** Two test files previously failed to load at
  all, and three asserted `spec_version === "1.2"` against an SDK emitting
  `1.3`. Assertions are now anchored to the SDK's exported `SPEC_VERSION`, so
  the suite cannot go stale against the spec again.
- Added regression coverage for namespaced Sparkplug tags — the exact case no
  test exercised, which is why the inference bug survived.

---

## @iaes/sdk 0.3.0 · iaes (Python) 0.3.0

### Fixed

- Default ingest path `/api/v1/iaes/ingest` → **`/iaes/ingest`** (see above).
  Exported as `DEFAULT_INGEST_PATH`.

### Added

- `publishBatch` / `publish_batch` reject batches over **100** events locally
  (`MAX_BATCH_SIZE`) instead of letting the server discard the whole batch.
- `IngestResponse` accepts `"dropped"` as a per-event status, with the server's
  `reason` — previously the type claimed only `stored | duplicate | error`.
