```
IAES                                                        G. Garza
Request for Comments: 010                                   Wertek AI
Category: Standards Track                              October 2026
ISSN: N/A

        Declaring When an Asset Is Down: The Facts MTBF and MTTR Need
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

**State: Draft**, per `GOVERNANCE.md` §6. Open for comment.
**Compatibility: MINOR** under `GOVERNANCE.md` §4.1 and §4.4, analysed part by
part in §9, with two dependencies that must be decided first (§8).
**Target version: none stated yet** -- the steward states one when this memo
moves to Review. Distribution is unlimited.

Numbered 010 because an open draft already holds 009 (the Appendix C memo).

# Copyright Notice

Copyright (c) 2026 Wertek AI. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

Plants report maintenance in MTBF, MTTR and availability. Today an IAES
consumer cannot compute any of them from IAES events alone in a way a second
consumer would reproduce. IAES can say that a **condition** became abnormal and
recovered, and how long was spent on a work order; it cannot say when the
**asset** stopped being able to perform, when it was restored, or what it was
doing while up. The specification also claims more than it carries: it says
recovery events "enable consumers to compute Mean Time To Recovery (MTTR)", and
the recovery of a condition is not the restoration of an asset.

This memo proposes how a producer declares those facts -- the timeline that
ISO 14224:2016 asks to be collected -- as a new event type, `asset.state`. **It
puts no indicator into IAES.** IAES carries the facts; how a consumer turns them
into MTBF or MTTR stays the consumer's, as `GOVERNANCE.md` §1 requires.

# Table of Contents

    1. The problem, measured against the specification
    2. What ISO 14224:2016 asks to be collected
    3. The boundary: facts, not indicators
    4. One acronym, three meanings
    5. Option A -- the down interval on maintenance.completion
    6. Option B -- a new event type, asset.state
    7. Recommendation
    8. Dependencies to decide first
    9. Compatibility level, part by part
    10. Effect on existing implementers
    11. Proposed incorporation
    12. What this memo does not decide
    13. Open questions

# 1. The problem, measured against the specification

Measured on `main` at `4539361` (2026-10-06):

1. **A recovered condition is presented as a basis for MTTR.** `IAES_SPEC.md`,
   *Recovery Events*: an `asset.health` event MAY represent recovery when "a
   previously abnormal condition returns to acceptable parameters", and this
   "enables consumers to compute Mean Time To Recovery (MTTR)". A power factor
   that drops and recovers while the bank keeps running has an onset and a
   recovery and **no down time at all**; a bearing can show an abnormal
   condition for weeks while the pump keeps pumping. The gap between onset and
   recovery measures how long a condition lasted. It is not the time to restore
   a failed item.
2. **`maintenance.completion` carries time spent, not down time.**
   `actual_duration_seconds` is "Actual time spent on the work order in seconds"
   (`schema/maintenance-completion.schema.json`). It does not say whether that is
   person-time or elapsed time, and nothing says when the asset went down or came
   back.
3. **`failure_confirmed` is not "a failure happened".** It is "Whether the
   predicted failure mode was confirmed during maintenance" (same schema). A
   consumer that counts failures by it counts confirmed predictions.
4. **`asset.health.estimated_downtime_hours` is an estimate**, made before the
   repair.
5. **Nothing says what an up asset was doing.** An MTBF over operating time
   (§2) needs to know running from standby. No IAES event can say which it was.

The consequence is not that consumers cannot compute MTBF and MTTR; it is that
each one computes them from a different proxy (onset-to-recovery, time spent on
the work order, calendar time, confirmed predictions), and two consumers reading
the same events report different numbers for the same asset. That is the
failure an interchange standard exists to prevent.

The trigger was practical: SCADA/MES integrators -- the audience of the Ignition
reference scenario (`scenarios/ignition/`) -- compute these indicators where the
run, stop and trip state of each asset already lives.

# 2. What ISO 14224:2016 asks to be collected

ISO 14224:2016 is in `references/registry.json`. This section cites it by
clause and does not reproduce its text.

- **3.15 down state** and **3.96 up state** -- unable / able to perform as
  required. A down state can be caused by a fault **or by preventive
  maintenance**.
- **3.16 down time** and **3.97 up time** -- the intervals in those states. Down
  time runs from the failure to the restoration of service and is planned or
  unplanned.
- **Table 4 (timeline definitions)** -- total time splits into down time
  (planned: preventive maintenance and other planned outages; unplanned:
  corrective maintenance and other unplanned outages) and up time, which lists
  start-up, running, run-down, hot standby, idle and cold standby.
- **8.3.1 (surveillance and operating period)** -- an item that is **idle** or in
  **hot standby** (ready for immediate operation when started) is considered
  **operating** ("in service"); an item in **cold standby** (needs activities
  before it can operate) is not. Table 4 lays the same leaves out next to
  "non-operating time", so a reader of the table alone can classify idle and hot
  standby the other way. **Two consumers can disagree on operating time while
  both citing ISO 14224.** §6 is designed so that they do not have to.
- **8.3.3 and Figure 4 (maintenance times)** -- two calendar times are
  recommended: **down time** (from the item being stopped for repair until it is
  back in its intended service, tested) and **active repair time** (the item
  being worked on).
- **3.60 mean elapsed time between failures** -- between failures in calendar
  time. Its Note 2 cites IEC 60050-192:2015, 192-05-13, which defines MTBF (also
  MOTBF) as the mean **operating** time between failures. Both are in use, and
  they need different facts.
- **3.61 MRT, 3.63 MTTR, 3.64 MTTRes** -- mean overall repairing time, mean time
  to repair and mean time to restoration differ by which parts of the down
  interval they include. 3.63 Note 4 observes that in practice only MRT and the
  mean active repair time can be collected.

Two facts are missing from IAES, and they are the ones 8.3.3 names first: **the
down interval**, planned or unplanned; and, for an MTBF over operating time,
**what the asset was doing while up**. The second time of 8.3.3, active repair
time, IAES does not carry either: `actual_duration_seconds` is "time spent",
which may be person-time (§1, item 2).

# 3. The boundary: facts, not indicators

`GOVERNANCE.md` §1: "if a rule needs a specific vendor's catalog, network, or
judgment to be meaningful, it is not part of IAES." A formula for MTBF needs
judgments IAES must not make for a plant: which failures count, over what
population and period, with what censoring, and -- §2 -- whether idle and hot
standby count as operating. So:

- IAES defines how to **declare** that an asset was up or down, planned or
  unplanned, and in which mode while up.
- IAES does **not** define MTBF, MTTR or availability, nor which modes count as
  operating time. A non-normative example may show a computation and must say
  which classification it used.
- How a producer **infers** a state from its signals (a trip bit, a current
  threshold, an operator's entry) is the producer's business and stays out.

This fits `IAES_SPEC.md` *Producers*: "IAES begins where interpretation begins".
Telling running from tripped, and a trip from a planned stop, is interpretation;
the system that does it -- a SCADA with that logic, a CMMS for planned outages,
an operator -- is the producer.

# 4. One acronym, three meanings

"MTTR" is not one quantity: ISO 14224:2016 3.63 uses it for mean time to
**repair**; IEC 60050-192, cited in 3.64, uses it for mean time to
**restoration**; and `IAES_SPEC.md` *Recovery Events* uses it for "Mean Time To
**Recovery**", which is neither. This memo uses the long names, and §11 removes
the acronym from the specification's text rather than redefining it.

# 5. Option A -- the down interval on maintenance.completion

Three optional fields on `maintenance.completion`:

| Field | Type | Meaning |
|---|---|---|
| `down_started_at` | RFC 3339 | when the asset entered the down state this work order addressed |
| `restored_at` | RFC 3339 | when the asset was back in its intended service |
| `downtime_category` | `planned` \| `unplanned` | Table 4's two branches of down time |

**Worked example.** A pump trips at 06:10, a technician works on it from 08:00
to 10:00, and it is back in service, tested, at 10:40:

```json
{
  "spec_version": "2.1",
  "event_type": "maintenance.completion",
  "event_id": "9a1e6f0b-3c2d-4e5f-8a9b-0c1d2e3f4a5b",
  "correlation_id": "5b4c3d2e-1f0a-4b9c-8d7e-6f5a4b3c2d1e",
  "timestamp": "2026-10-06T10:45:00Z",
  "source": "acme.cmms",
  "asset": {"asset_id": "PUMP-101"},
  "data": {
    "work_order_id": "WO-2026-1101",
    "status": "completed",
    "down_started_at": "2026-10-06T06:10:00Z",
    "restored_at": "2026-10-06T10:40:00Z",
    "downtime_category": "unplanned"
  }
}
```

- **For:** smallest change; the CMMS that closes the work order often knows both
  times.
- **Against:** the facts arrive only when the work order closes, so nothing shows
  an asset as down while it is down; a trip reset by an operator with no work
  order has no event to carry it; and it says nothing about what the asset was
  doing while up, so **an MTBF over operating time stays impossible**. The
  elapsed MTBF (3.60) becomes computable only from unplanned down intervals --
  not from `failure_confirmed` (§1, item 3).

# 6. Option B -- a new event type, asset.state

A new published event type, emitted **once per transition**, never per reading
(the rule `sensor.registration` already follows). Its `data`:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `state` | `up` \| `down` | yes | 3.96 / 3.15, from this event's `timestamp` on |
| `down_kind` | `planned` \| `unplanned` | when `state` is `down` | Table 4's two branches of down time |
| `up_mode` | `start_up` \| `running` \| `run_down` \| `hot_standby` \| `idle` \| `cold_standby` | no | Table 4's up-time leaves, when `state` is `up` and the producer knows it |
| `detail` | string, open | no | anything finer: `preventive_maintenance`, `modification`, `corrective_maintenance`, `trip`, … (examples, not a published catalog) |
| `work_order_id` | string | no | the work order this down interval is being handled under, when there is one |
| `reason` | string | no | free text: what the producer observed |

The design declares the **mode**, not a verdict on whether it is operating time.
A consumer computing an MTBF over operating time states which modes it counted
-- ISO 14224:2016 8.3.1 counts `idle` and `hot_standby`; a reader of Table 4
alone may not -- and two consumers with the same events and the same stated
classification get the same number. Neither has to guess what the producer
meant.

The envelope already says when: `timestamp` is "When the event occurred"
(`IAES_SPEC.md`, envelope table). A state holds until the next `asset.state` for
the same asset **from the same `source`** (§13 item 3). A transition out of a
down state SHOULD reference the event that opened it with `source_event_id` and
share its `correlation_id`. A work order keeps its own chain
(intent → completion, `IAES_SPEC.md` *Typical Flow*); the link between a down
interval and its work order is `work_order_id`, not the chain.

**Worked example.** The same trip, as it happens:

```json
[
  {"spec_version": "2.1", "event_type": "asset.state",
   "event_id": "1c7f2a90-6b1e-4d3a-9f5c-2e8d4b6a0c11", "correlation_id": "e0b9a8c7-d6e5-4f43-a2b1-c0d9e8f7a6b5",
   "timestamp": "2026-10-06T06:10:00Z", "source": "plant.scada",
   "asset": {"asset_id": "PUMP-101"},
   "data": {"state": "down", "down_kind": "unplanned", "detail": "trip", "reason": "motor protection trip"}},

  {"spec_version": "2.1", "event_type": "asset.state",
   "event_id": "4d2b8e61-0a9f-4c7e-b3d5-6f1a2c8e9b07", "correlation_id": "e0b9a8c7-d6e5-4f43-a2b1-c0d9e8f7a6b5",
   "source_event_id": "1c7f2a90-6b1e-4d3a-9f5c-2e8d4b6a0c11",
   "timestamp": "2026-10-06T10:40:00Z", "source": "plant.scada",
   "asset": {"asset_id": "PUMP-101"},
   "data": {"state": "up", "up_mode": "running", "work_order_id": "WO-2026-1101"}}
]
```

Any consumer gets the same unplanned down interval (4 h 30 min) and, because
every up interval carries its mode, the same operating time between this failure
and the next under whichever classification it states.

- **For:** it is what a SCADA, a PLC or an edge gateway already knows, at the
  moment it changes; a dashboard can show an asset as down while it is down; a
  trip with no work order is still declared; and it is the only option that
  makes both MTBFs computable -- elapsed (3.60) and operating (IEC 60050-192).
- **Against:** a new schema, a new model class in both SDKs, flow nodes that can
  set `timestamp` (§10), and producer guidance (start-up, several producers --
  §13).

**Fields that already say something close, and why they are not the record:**
`asset.hierarchy.is_active` says whether the asset is in the register's active
set (a lifecycle fact, not up/down); `asset.health.iso_13374_status: failed` is a
**condition** assessment. Neither declares an interval, and §11 says so in the
specification so that a consumer does not derive down time from them.

# 7. Recommendation

**Option B.** Option A records the down interval after the fact, from the
system that closed the work; Option B records the timeline as it happens, from
the system that sees it, and only B covers what the asset was doing while up. A
standard should carry the fact where it is born. If a producer exists that can
send completions with the interval but cannot emit `asset.state`, Option A's
fields can be added later as a fallback, with a rule for which source wins
(§13 item 4).

**Active repair time** (8.3.3) gets its own optional field on
`maintenance.completion`, `active_repair_seconds`: the elapsed time the item was
being worked on (Figure 4). `actual_duration_seconds` is **left as it is**.
Redefining it as active repair time would change what existing bytes mean when
two technicians work two hours (four hours spent, two hours of active repair),
which is MAJOR under `GOVERNANCE.md` §4.2.

# 8. Dependencies to decide first

1. **How canonical JSON escapes non-ASCII text.** `content_hash` is "canonical
   JSON, sorted keys" (`IAES_SPEC.md`), and the two SDKs disagree on any string
   with a non-ASCII character: the Python SDK escapes it and the TypeScript SDK
   does not (measured 2026-10-06 on "disparo de protección": `8af73ebab2507204`
   against `35bfe554a215913c`; on ASCII they agree). `asset.state.reason` is free
   text, so a non-English plant hits it on day one. That decision is normative
   and needs its own memo; this one should not ship before it.
2. **Whether a MINOR may change the bytes served at a major's schema URI.**
   Adding `active_repair_seconds`, and listing `asset.state` among the envelope's
   `event_type.examples`, edit two schemas published under `/schema/v2/`.
   `GOVERNANCE.md` §8 item 1 says published versions are never edited in place
   and stays silent on whether a per-major URI carries the latest minor. Either
   that is stated (and the earlier bytes stay retrievable at the release tag and
   DOI), or 2.1 ships `asset.state` as a new schema only and the two additions
   wait.

Not a dependency of this memo but found while writing it: every published event
schema references the envelope as `iaes-envelope.schema.json`, which does not
resolve under `https://iaes.dev/schema/v2/` (the envelope is served as
`/schema/v2/envelope`). A new `asset-state.schema.json` copied from an existing
one would inherit it.

# 9. Compatibility level, part by part

- **The new event type `asset.state`: MINOR**, `GOVERNANCE.md` §4.1 -- consumers
  are already required to tolerate unknown `event_type` values.
- **`active_repair_seconds` on `maintenance.completion`: MINOR**, §4.1 -- an
  optional field.
- **Removing the MTTR sentence from *Recovery Events*, and adding that a
  condition's recovery MUST NOT be presented as an asset's restoration:** this
  is normative text, so §4.1's "non-normative text" line does not cover it; it
  is classified by §4.4.
  - **T1 (meaning).** The bytes of a recovery event keep the meaning 2.0 gave
    them: a condition returned to acceptable parameters. What changes is a
    statement about a quantity a consumer may derive from them. The steward
    should confirm in Review that a statement about a derived quantity is not a
    stated meaning of the bytes; if it is judged to be one, this part is MAJOR
    and should wait for 3.0.
  - **T2 (cross-version).** A consumer declaring 2.1 can still consume a 2.0
    recovery event with the meaning 2.0 gave it. So, if T1 does not answer, the
    obligation is **MINOR**, and only implementations that declare 2.1 must
    adopt it; a 2.0 consumer that labels onset-to-recovery as MTTR stays
    conforming to 2.0.
- **The SDK profile requiring the new class.** `surface.json` counts published
  types from `schema/` (enforced by `tests/test_surface.py`), so publishing the
  schema makes the 2.1 profile require the class. `GOVERNANCE.md` has no rule
  for profile changes; RFC-006 anticipated that adding a required capability
  would be confirmed under §4.4. Proposed: the 2.1 profile requires it; an SDK
  that claims the 2.0 profile keeps claiming 2.0. No implementation claims the
  profile today (`implementations.json`), so nothing breaks.

# 10. Effect on existing implementers

- **Producers:** nothing changes for any existing event. A producer that knows
  run/stop state MAY start emitting `asset.state`.
- **Consumers:** unknown types are already tolerated. A consumer that derives an
  "MTTR" from onset-to-recovery keeps working; once it declares 2.1 it stops
  presenting that number as the asset's restoration.
- **SDKs:** a model class, an enum for `state` (not named `AssetState`, which the
  class takes), enums for `down_kind` and `up_mode`, the schema copy, and the
  three internal lists of published types in each SDK -- which today can go out
  of step silently; the implementation PR should add a guard that derives them
  from `schema/`.
- **Node-RED and n8n:** neither lets a flow set the envelope `timestamp` today.
  For `asset.state` the timestamp **is** the fact, so both need it before they
  can produce this type truthfully.
- **Reference scenarios:** the five-event story is unchanged, but its
  `spec_version` moves to 2.1 with the release (the fixture and the Ignition
  builder, which writes `"2.0"` by hand). A second scenario -- a trip, its
  repair and the return to operation -- gets its own fixture, and there
  `timestamp` cannot be volatile: the interval is what is being tested.
- **Text that repeats the claim this memo corrects:** besides *Recovery
  Events*, `scenarios/ignition/README.md` calls the mean of
  `actual_duration_seconds` "MTTR" and the gap between completions with
  `failure_confirmed` "MTBF". Both are corrected with this memo.

# 11. Proposed incorporation

When Accepted, in the same change (precedent: RFC-008):

- `schema/asset-state.schema.json` (new, `$id` `https://iaes.dev/schema/v2/asset.state`), and its copies in both SDKs.
- `schema/maintenance-completion.schema.json`: `active_repair_seconds` -- subject to §8 item 2.
- `schema/iaes-envelope.schema.json`: `asset.state` in `event_type.examples` -- subject to §8 item 2.
- `IAES_SPEC.md`: a section for `asset.state`; a row in the event type usage
  guide and in *Producers*; *Recovery Events* without the MTTR sentence and with
  the MUST NOT; a sentence that `asset.hierarchy.is_active` and
  `iso_13374_status` are not an up/down record; `active_repair_seconds` in the
  completion table; the version history row.
- `surface.json`: published types and vocabulary counts for 2.1 (§9).
- `GOVERNANCE.md` §9.2, which names "IAES 2.0" as the release that adopts the profile.
- `references/registry.json`: IEC 60050-192:2015.

# 12. What this memo does not decide

- Any formula for MTBF, MTTR, MTTRes, MRT or availability, and any threshold.
- Which up modes count as operating time.
- Which states a given equipment class can have, or how a producer infers them.
- A published catalog for `detail` (`GOVERNANCE.md` §7).
- Partial work-order status updates, which `IAES_SPEC.md` lists as not yet
  supported.

# 13. Open questions

1. **Name.** `asset.state` or `asset.availability`? The first names what is
   declared; the second names one use of it.
2. **Unknown at start.** When a producer starts and does not know the previous
   state, does it emit its current state with a `reason` saying so, or stay
   silent until the first transition? The answer decides whether the first span
   of a series can be trusted.
3. **Several producers.** A SCADA declares trips and a CMMS declares planned
   outages for the same asset. This memo keys a timeline by asset **and**
   `source`; is a single merged timeline per asset needed, and if so, with what
   precedence?
4. **Option A as a fallback?** Is there a producer that can send completions with
   the down interval but cannot emit `asset.state` (a CMMS with no SCADA behind
   it)?

# Author

Gilberto Garza, Wertek AI -- steward of IAES.
