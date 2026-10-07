# Changelog

All four IAES packages are versioned together (`GOVERNANCE.md` §3.1).

- `node-red-contrib-iaes` (npm) — the Node-RED palette
- `n8n-nodes-iaes` (npm) — the n8n nodes
- `@iaes/sdk` (npm) — TypeScript SDK
- `iaes` (PyPI) — Python SDK

The normative history of the specification is the version history in `IAES_SPEC.md`; this file records the packages.

---

## 2.1.0 — 2026-10-07, implementing IAES 2.1

The four packages move to **2.1.0** together (`GOVERNANCE.md` §3.1): they
implement IAES 2.1, which accepts RFC-010, RFC-011 and RFC-013. The version
history in `IAES_SPEC.md` has the specification's side; this is the packages'.

### Events now declare 2.1

`SPEC_VERSION` is `"2.1"` in both SDKs, so every event they build declares 2.1
and its `content_hash` is computed by RFC 8785 (below). **For ASCII text and
ordinary numbers the hash is the same as in 2.0.x**; it changes where the 2.0
implementations disagreed: non-ASCII text, exponents, integer-like keys and
characters outside the BMP. An event built by 2.0.x and retried by 2.1.0 still
declares 2.0, and keeps its 2.0 hash.

### `asset.state` (IAES-RFC-010)

- **Python and TypeScript:** `AssetState`, which never carries `content_hash`.
  `timestamp` is **required**: for this type it is the instant of the
  transition, and a default of "now" would produce a valid event and a wrong
  down interval. Omitting it raises `TypeError` (Python) or throws (TypeScript,
  where `AssetStateInit.timestamp` is also required by the type). In
  TypeScript `toJSON()` returns `IAESWireEnvelope`, whose `content_hash` is
  optional, and `fromObject` / `fromJSON` accept either envelope type.
- **Five enumerations,** generated from the schema: `UpDownState`, `DownKind`
  and `PreviousState` (closed), `DownCause` and `UpMode` (advisory: the fields
  are open, and any other value is *not classified*, never an error). Not
  `AssetState`: the class takes that name.
- **Node-RED `iaes route`:** output 8, `state`. It comes after the other
  seven, so a flow wired before 2.1 keeps every wire. **But `asset.state`
  moves:** with a 2.0 package it left by output 7, `other` (an unknown type),
  and from 2.1.0 it leaves by output 8. A 2.0 flow that handled it on output 7
  drops it after the upgrade until output 8 is wired.
- **Not yet:** the Node-RED and n8n nodes do not build `asset.state`. Neither
  lets a flow set the envelope timestamp, which for this type is the fact
  (`implementations.json`).
- **A second reference story,** the trip of RFC-010's example, told by both
  SDKs and checked with its timestamps (`scenarios/fixture-asset-state.json`).
- **Ignition scenario:** declares 2.1 and serialises by RFC 8785 itself, since
  `json.dumps` is not JCS. Reproduces every shared JCS vector on CPython
  (`tests/test_ignition_jcs.py`: 34 accepted, 3 refused), and all 37 in Jython
  on a real Ignition 8.3.9 Gateway (2026-10-07). That Gateway run found that
  Jython's `repr(float)` is Java's `Double.toString`, not the shortest form
  (`1e23` → `9.999999999999999e+22`); the serialiser now takes the fewest
  correctly rounded digits that read back as the same double.

### Migration for consumers on a 2.0.x SDK

The 2.0.x SDKs' `from_object` (Python, `models.py`) and `fromObject`
(TypeScript, `models.ts`) raise `Unknown IAES event_type` on an `asset.state`
event: they dispatch only the types they know. A consumer that passes every
incoming event through them either guards that call or takes the 2.1.0
packages. Nothing else on the wire needs a migration (`IAES_SPEC.md`, version
history).

### Before the cut: findings of an adversarial review

Four reviewers read the release candidate before it was tagged. What changed:

- **Integers in `content_hash`.** RFC 8785 works on IEEE-754 doubles. The
  Python SDK and the Ignition script refused any integer above 2**53, so a
  builder refused `value=10**16` while the TypeScript SDK hashed it. Now an
  integer is hashed as the double nearest to it, as `JSON.parse` reads it
  (`9007199254740993` as `9007199254740992`), and only one beyond the largest
  double is refused. The specification now says so, and that producers should
  not rely on the hash to tell apart integers a double cannot represent.
- **Lone surrogates.** RFC 8785 serialises I-JSON, which has none. TypeScript
  escaped and hashed them; Python failed with a codec error. Both now refuse
  them with a clear error, and so does the Ignition script.
- **Which rule a `spec_version` selects.** TypeScript hashed an absent version,
  `3`, `2.1-rc` and `2.1a` by RFC 8785; Python by the 2.0 rule. Both now read
  the version with the same expression, `^2\.([0-9]+)$`: RFC 8785 for a minor
  of 1 or more, the 2.0 rule for anything else. In TypeScript an explicitly
  absent version (`computeContentHash(data, event.spec_version)` on an event
  without one) is now absent, not this SDK's version.
- **TypeScript `canonicalJson`** throws on a `Date`, `Map`, `Set` or class
  instance instead of writing it as `{}` or a string.
- **`asset.state` contract**, tightened before the schema is served anywhere:
  an `up` event carries no `down_kind` or `down_cause`, a `down` event no
  `up_mode`, `down_kind` is never null, and the event declares 2.1 or a later
  2.x minor. `tools/check_schema_compat.py` now reads the last release tag,
  so it reports and does not block a narrowing of a schema that is in no
  release yet; a released schema is guarded as before.
- **New shared cases:** 23 more `content_hash` vectors (number boundaries,
  U+2028/U+2029, U+007F, an escaped solidus in the source, key U+FFFF, nulls
  and empty containers, three refusals, six version switches) and 7 more
  validation cases for `asset.state`.

### Ranges kept on purpose

`node-red-contrib-iaes` and `n8n-nodes-iaes` keep `"@iaes/sdk": "^2.0.0"` in
this change. Their lockfiles resolve the SDK from the registry, and 2.1.0 does
not exist there until it is published; CI tests them against the SDK in this
commit (`file:../npm`). The range moves to `^2.1.0` after the SDK is published,
as the 2.0 lockfiles did.

### `content_hash` by RFC 8785 (JCS) for 2.1 events (IAES-RFC-011)

Both SDKs now carry `canonical_json` / `canonicalJson` (RFC 8785).
`compute_content_hash` / `computeContentHash` take the `spec_version` of the
event:

- 2.1 and later use JCS;
- 2.0 and earlier keep the 2.0 computation unchanged.

Written ahead of 2.1 while the SDKs still declared 2.0; with 2.1.0 they
declare 2.1, and the rule applies (above).

`conformance/content_hash.json` gains the JCS bytes for every case, plus
RFC 8785's own example. Measured on the shared cases:

- **Python** differed from JCS on 6 of 11: escaping, exponents, key order
  outside the BMP.
- **TypeScript** differed on 1: integer-like keys, because it built a sorted
  object and JavaScript enumerates integer-like keys first. It now writes the
  members in order.

### Shape rules are generated from `schema/`, never copied

`tools/generate_from_schema.py` writes the published types, their schema files,
the required data fields and the closed catalogues, plus both SDKs'
enumerations. It writes them into `src/iaes/_from_schema.py`,
`src/iaes/enums.py`, `npm/src/fromSchema.ts` and `npm/src/enums.ts`. The SDKs
import from those files, and `tests/test_rules_live_in_the_schema.py` fails if
a generated file is stale or a catalogue is copied by hand elsewhere.

- **The enumerations are unchanged.** All ten are identical, member by member,
  to the hand-written ones. Their docstrings now come from the schema's
  descriptions.
- **New exports:** `CATALOGS` and `REQUIRED_DATA_FIELDS` in both SDKs.
- **n8n IAES Emit:** its option lists now come from the SDK. On the hand-written
  form, three fields did not match the schemas:
  - `iso_13374_status` had no `unknown`;
  - `triggered_by` had no `alert`;
  - `units_qualifier` was free text with the placeholder `peak-peak`, which the
    schema rejects. It is now a menu of the five values the schema allows.

  `measurement_type` now lists the SDK's seventeen advisory values; it listed
  fourteen.
- **Unchanged on purpose:** the Node-RED route node keeps its own ordered list.
  The position of a type is the output it leaves by, and deployed flows are
  wired to it.

### One set of cases for four implementations (`conformance/`)

The Python SDK, the TypeScript SDK, the Node-RED nodes and the n8n nodes now
run the same cases: 57 events with their expected verdicts and 11
`content_hash` payloads. Measured before this change, the four implementations
disagreed. Node-RED accepted `spec_version: "205"`. n8n's strict mode had its
own incomplete list of required fields. Node-RED rejected a non-UUID
`event_id` that the other validators accept. Python and TypeScript hashed six
of eleven payloads differently. See `conformance/README.md`.

- **New:** `find_nonconformities` (Python) and `findNonconformities`
  (TypeScript) name the fields the schemas accept and the specification forbids
  (identifiers that are not UUIDs, timestamps that are not RFC 3339 UTC, a
  `dataschema` that is not a URI). They read the schemas' `format`
  annotations and keep no field list of their own.
- **Python `validate`:** an event that is not an object raises
  `ValidationError("Event must be a JSON object")`, as TypeScript does. It used
  to raise `AttributeError`.
- **Node-RED `iaes-validate`:** judges with the SDK instead of its own rules.
  - The schema decides valid and invalid; `msg.iaes_nonconformities` names the
    nonconforming fields.
  - A new **Strict** option rejects nonconforming events. It is off for new
    nodes. A node saved before the option existed keeps rejecting them, as it
    did.
  - Error texts are now the SDK's: each names the field's path.
  - `spec_version: "205"` is now rejected.
- **n8n IAES Validate:** judges with the SDK.
  - The schema decides in both modes, so a missing required data field is now
    Invalid even with strict mode off.
  - Strict mode now also rejects nonconforming fields.
  - `iaes_validation.nonconformities` is new.
- `ajv` is now a dependency of `node-red-contrib-iaes` and `n8n-nodes-iaes`.
  The nodes validate with the SDK, which needs it.
- The `content_hash` disagreement is recorded case by case, not fixed. The
  fix is proposed as a draft RFC (RFC 8785, wertek-ai/iaes#57).

---

## 2026-09-09 — 2.0.2

### An absent score was written as 0.0 in every SDK

`asset.health` events whose producer supplied neither `anomaly_score` nor
`fault_confidence` went out with both set to `0.0` -- from the TypeScript SDK,
the Python SDK and, through its editor defaults, the Node-RED `iaes-health`
node. Under the fields' own meaning, `0.0` asserts *definitely normal* and
*no confidence*. IAES_SPEC.md (Producers 3) names this exact substitution as
the thing a producer MUST NOT do, and RFC-002 §6 recorded it as the real
defect when the range was decided.

Fixed in `npm/src/models.ts`, `src/iaes/models.py` and
`node-red/nodes/iaes-health.js` + `.html`: a score the producer did not give
is omitted from the wire; a supplied `0` is a score and stays. **The public
API is unchanged**: `AssetHealth(...).anomaly_score` still reads as a number,
`0.0` when nothing was given -- what a producer said is tracked beside the
instance and consulted only when serialising. Found by the reference
scenarios' cross-implementation `content_hash` check and the n8n schema-vs-
form census, which had to declare these two fields as the SDK's business.

Also in this release, from the reference scenarios: Node-RED's producer nodes
dropped `msg.correlation_id` (a chain became three), and the n8n emit node
could not say `units_qualifier` and gave optional fields defaults with a
meaning (`failure_confirmed: false`, `triggered_by: "threshold"`,
`recommended_due_days: 7`; and `0` was collapsed to "not set" for numerics
whose schema allows zero).

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

## n8n-nodes-iaes 0.2.0

### Fixed

- **La credencial `IAES API` entregaba el endpoint equivocado, ya pre-llenado.** Su
  `httpEndpoint` traía por defecto `https://api.wertek.ai/api/v1/iaes/ingest` — una ruta
  que ningún servidor implementa — y describía la llave como *"Bearer token"* cuando el
  ingest autentica con `X-API-Key`. `IaesEmit` sólo construye el envelope y no envía por
  sí mismo, así que **ese valor es el que el usuario copia a su nodo HTTP Request**: la
  URL rota se propagaba a mano. Llevaba así desde 0.1.1.

  > ⚠️ **Arreglar el default no arregla las credenciales ya guardadas.** Si configuraste
  > esta credencial antes de 0.2.0, corrige la URL a mano.

### Added

- La credencial ahora **inyecta `X-API-Key`** automáticamente (`authenticate: generic`)
  al usarse en un nodo HTTP Request, en vez de dejar el header al criterio de cada quien.

### Changed

- Depende de `@iaes/sdk@^0.3.0`.

---

## Packaging

- 🔴 **El sdist de Python pesaba 6.8 MB contra 26 KB del wheel.** `hatchling` barría el
  monorepo entero porque `.gitignore` cubría `npm/node_modules/` y
  `node-red/node_modules/` pero **no** `n8n-nodes/node_modules/`: **2,627 de 2,738
  archivos** del paquete eran dependencias de Node. Corregido declarando el contenido del
  sdist de forma explícita —así no depende de que el `.gitignore` esté completo— y
  cerrando el hueco del `.gitignore`. Ahora son **40 KB y 30 archivos**.
- **CI y publicación por OIDC.** `ci.yml` corre las cuatro suites en cada PR;
  `release.yml` publica por tag (`sdk-v*`, `nodered-v*`, `n8n-v*`, `py-v*`) usando
  Trusted Publishing de npm y PyPI — **sin tokens almacenados**, y comprobando que el tag
  y la versión del paquete coincidan antes de publicar.

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
