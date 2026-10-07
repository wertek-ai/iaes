```
IAES                                                        G. Garza
Request for Comments: 009                                   Wertek AI
Category: Standards Track                              October 2026
ISSN: N/A

        Declaring When an Asset Is Down: The Facts MTBF and MTTR Need
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

**State: Draft**, per `GOVERNANCE.md` §6. Open for comment.
**Compatibility: MINOR** under either option (§8). **Target version: not yet
stated** -- the steward states one when this memo moves to Review.
Distribution is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI, Inc. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

Plants report maintenance in MTBF, MTTR and availability. Today an IAES
consumer cannot compute any of them from IAES events alone in a way a second
consumer would reproduce: IAES can say that a **condition** became abnormal and
recovered, and how long a technician **worked** on a work order, but it cannot
say when the **asset** stopped being able to perform its function, when it was
restored, or whether it was operating in between. The specification also
claims more than it carries: it says recovery events "enable consumers to
compute Mean Time To Recovery (MTTR)", and the recovery of a condition is not
the restoration of an asset.

This memo proposes how a producer declares those facts -- the timeline that
ISO 14224:2016 asks to be collected -- and compares two shapes for it. **It does
not put an indicator into IAES.** IAES carries the facts; how a consumer turns
them into MTBF or MTTR stays the consumer's, as `GOVERNANCE.md` §1 requires.

# Table of Contents

    1. The problem, measured against the specification
    2. What ISO 14224:2016 asks to be collected
    3. The boundary: facts, not indicators
    4. Option A -- the down interval on maintenance.completion
    5. Option B -- a new event type, asset.state
    6. Recommendation
    7. The text this memo corrects
    8. Compatibility level of this change
    9. Effect on existing implementers
    10. What this memo does not decide
    11. Open questions

# 1. The problem, measured against the specification

Measured on `main` at `4539361` (2026-10-06):

1. **A recovered condition is presented as a basis for MTTR.** `IAES_SPEC.md`,
   *Recovery Events*: an `asset.health` event MAY represent recovery when "a
   previously abnormal condition returns to acceptable parameters", and this
   "enables consumers to compute Mean Time To Recovery (MTTR)". A power factor
   that drops and recovers while the bank keeps running has an onset and a
   recovery and **no down time at all**. A bearing can show an abnormal
   condition for weeks while the pump keeps pumping. Measuring the gap between
   onset and recovery measures how long a condition lasted, which is useful,
   and is not the time to restore a failed item.
2. **`maintenance.completion` carries work time, not down time.** Its optional
   `actual_duration_seconds` is "Actual time spent on the work order in
   seconds" (`schema/maintenance-completion.schema.json`). Nothing says when the
   asset went down or came back.
3. **`asset.health` carries an estimate, not a fact.** `estimated_downtime_hours`
   is "Estimated repair duration" -- a prediction made before the repair.
4. **Nothing distinguishes operating from not operating.** The MTBF that
   ISO 14224:2016 points to is defined over **operating** time between failures,
   not calendar time (§2). An idle pump in cold standby is up and not
   operating; counting its idle months as operating time inflates that MTBF. No
   IAES event can say which it was.

The consequence is not that consumers cannot compute MTBF and MTTR; it is that
each one computes them from a different proxy (onset-to-recovery, work-order
duration, calendar time), and two consumers reading the same events report
different numbers for the same asset. That is the failure an interchange
standard exists to prevent.

The trigger was practical: SCADA/MES integrators, the audience of the Ignition
reference scenario (`scenarios/ignition/`), compute these indicators in the
Gateway, where the run/stop/trip state of each asset already lives.

# 2. What ISO 14224:2016 asks to be collected

ISO 14224:2016 is in `references/registry.json` as available. This section
cites it by clause and does not reproduce its text.

- **3.15 down state** and **3.96 up state** -- unable / able to perform as
  required. A down state can be caused by a fault **or by preventive
  maintenance**.
- **3.16 down time** -- the interval in the down state, from the failure to the
  restoration of service; it is planned or unplanned.
- **Table 4 (timeline definitions)** -- total time splits into **down time**
  (planned: preventive maintenance and other planned outages; unplanned:
  corrective maintenance and other unplanned outages) and **up time**
  (operating time: start-up, running, run-down; non-operating time: hot
  standby, idle, cold standby).
- **8.3.3 and Figure 4 (maintenance times)** -- two calendar times are
  recommended for collection: **down time** (from the equipment being stopped
  for repair until it is back in its intended service, tested) and **active
  repair time**.
- **3.61 MRT, 3.63 MTTR, 3.64 MTTRes** -- mean overall repairing time, mean time
  to repair and mean time to restoration differ by which parts of the down
  interval they include. 3.63 Note 4 observes that in practice only MRT and the
  mean active repair time can be collected.
- **3.60 mean elapsed time between failures** -- between failures in
  **calendar** time. Its Note 2 cites IEC 60050-192's definition of MTBF (also
  MOTBF) as the mean **operating** time between failures. Both are in use, and
  they need different facts: the elapsed one needs only the failures; the
  operating one also needs which up time was operating time.
- **Annex C** builds availability and the reliability parameters from these
  times.

So two facts are missing from IAES, and they are exactly the ones 8.3.3 names
first: **the down interval** (with planned/unplanned), and, for an MTBF over
operating time, **which up time was operating time**. The second of 8.3.3's two times, active repair
time, IAES already carries as `actual_duration_seconds`.

# 3. The boundary: facts, not indicators

`GOVERNANCE.md` §1: "if a rule needs a specific vendor's catalog, network, or
judgment to be meaningful, it is not part of IAES." A formula for MTBF needs
judgments IAES must not make for a plant: which failures count, over what
population and period, with what censoring (Annex C discusses all three). So:

- IAES defines how to **declare** that an asset entered and left a down state,
  planned or unplanned, and whether it was operating.
- IAES does **not** define MTBF, MTTR or availability, nor publish a formula. A
  non-normative example may show a computation, as the reference scenarios
  show events, and says so.
- The states are ISO 14224's generic timeline categories, which need no
  vendor's catalog. How a producer **infers** a state from its signals (a trip
  bit, a current threshold, an operator's button) is the producer's business
  and stays out.

# 4. Option A -- the down interval on maintenance.completion

Add three optional fields to `maintenance.completion`, and clarify one:

| Field | Type | Meaning |
|---|---|---|
| `down_started_at` | RFC 3339 | when the asset entered the down state this work order addressed |
| `restored_at` | RFC 3339 | when the asset was back in its intended service |
| `downtime_category` | `planned` \| `unplanned` | Table 4's two branches of down time |
| `actual_duration_seconds` | *(existing)* | clarified: **active** repair or maintenance time (8.3.3, Figure 4), not down time |

**Worked example.** A pump trips at 06:10, a technician works on it from 08:00
to 10:00, and it is back in service, tested, at 10:40:

```json
{
  "spec_version": "2.0",
  "event_type": "maintenance.completion",
  "event_id": "9a1e6f0b-3c2d-4e5f-8a9b-0c1d2e3f4a5b",
  "correlation_id": "5b4c3d2e-1f0a-4b9c-8d7e-6f5a4b3c2d1e",
  "timestamp": "2026-10-06T10:45:00Z",
  "source": "acme.cmms",
  "asset": {"asset_id": "PUMP-101"},
  "data": {
    "work_order_id": "WO-2026-1101",
    "status": "completed",
    "actual_duration_seconds": 7200,
    "down_started_at": "2026-10-06T06:10:00Z",
    "restored_at": "2026-10-06T10:40:00Z",
    "downtime_category": "unplanned",
    "failure_confirmed": true
  }
}
```

Down time 4 h 30 min; active repair time 2 h. A consumer computing MRT or MDT
over completions now gets the same number as any other consumer.

- **For:** smallest change; the CMMS that closes the work order usually knows
  both times; no new event type.
- **Against:** the facts arrive only when the work order closes, so a dashboard
  cannot show an asset as down while it is down. A down interval with no work
  order (a trip reset by an operator) has no event to carry it. The elapsed MTBF
  (3.60) becomes computable from completions with `failure_confirmed`; it says
  nothing about operating time, so **the operating MTBF stays impossible**.

# 5. Option B -- a new event type, asset.state

A new published event type, emitted **once per transition**, never per
reading (the same rule `sensor.registration` follows):

| Field | Type | Required | Meaning |
|---|---|---|---|
| `state` | `operating` \| `non_operating` \| `down_planned` \| `down_unplanned` | yes | the asset's state from this event's `timestamp` on (Table 4's four leaves at the second level) |
| `detail` | string, open catalog | no | the third level, if the producer knows it: `start_up`, `running`, `run_down`, `hot_standby`, `idle`, `cold_standby`, `preventive_maintenance`, `modification`, `corrective_maintenance`, `shutdown`, … |
| `reason` | string | no | free text: what the producer observed (a trip bit, an operator's entry) |

The envelope already says when: `timestamp` is "When the event occurred"
(`IAES_SPEC.md`, envelope table). A state holds until the next `asset.state`
for the same asset. A transition **out of** a down state SHOULD reference the
event that opened it with `source_event_id` and share its `correlation_id`, so
a down interval is reconstructed by the same chain rule the specification
already uses; a `maintenance.completion` for the repair joins the same chain.

**Worked example.** The same trip, told as it happens:

```json
[
  {"spec_version": "2.0", "event_type": "asset.state",
   "event_id": "1c7f2a90-6b1e-4d3a-9f5c-2e8d4b6a0c11", "correlation_id": "e0b9a8c7-d6e5-4f43-a2b1-c0d9e8f7a6b5",
   "timestamp": "2026-10-06T06:10:00Z", "source": "plant.scada",
   "asset": {"asset_id": "PUMP-101"},
   "data": {"state": "down_unplanned", "detail": "shutdown", "reason": "motor protection trip"}},

  {"spec_version": "2.0", "event_type": "maintenance.completion",
   "event_id": "9a1e6f0b-3c2d-4e5f-8a9b-0c1d2e3f4a5b", "correlation_id": "e0b9a8c7-d6e5-4f43-a2b1-c0d9e8f7a6b5",
   "source_event_id": "1c7f2a90-6b1e-4d3a-9f5c-2e8d4b6a0c11",
   "timestamp": "2026-10-06T10:00:00Z", "source": "acme.cmms",
   "asset": {"asset_id": "PUMP-101"},
   "data": {"work_order_id": "WO-2026-1101", "status": "completed",
            "actual_duration_seconds": 7200, "failure_confirmed": true}},

  {"spec_version": "2.0", "event_type": "asset.state",
   "event_id": "4d2b8e61-0a9f-4c7e-b3d5-6f1a2c8e9b07", "correlation_id": "e0b9a8c7-d6e5-4f43-a2b1-c0d9e8f7a6b5",
   "source_event_id": "1c7f2a90-6b1e-4d3a-9f5c-2e8d4b6a0c11",
   "timestamp": "2026-10-06T10:40:00Z", "source": "plant.scada",
   "asset": {"asset_id": "PUMP-101"},
   "data": {"state": "operating", "detail": "running"}}
]
```

From these three events any consumer gets the same down time (4 h 30 min,
unplanned), the same active repair time (2 h), and -- because every
`operating` / `non_operating` span is declared -- the same operating time
between this failure and the next one.

- **For:** it is what a SCADA, a PLC or an edge gateway already knows, at the
  moment it changes; a dashboard can show an asset as down while it is down; a
  trip with no work order is still declared; and it is the only option that
  makes both MTBFs computable -- elapsed (3.60) and operating (IEC 60050-192).
- **Against:** a new schema, a new model class in both SDKs, and producer
  guidance to write (once per transition; what to do at start-up when the
  previous state is unknown -- see §11).

# 6. Recommendation

**Option B**, plus Option A's **clarification** of `actual_duration_seconds` as
active repair time. Option A's three new fields are then unnecessary: the down
interval is the span between two `asset.state` events, and declaring it a
second time on the completion would create two sources for one fact that could
disagree.

The reasoning, in one line: Option A records the down interval after the fact,
from the system that closed the work; Option B records the timeline as it
happens, from the system that sees it, and only B covers operating time. A
standard should carry the fact where it is born.

# 7. The text this memo corrects

In `IAES_SPEC.md`, *Recovery Events*, the sentence "This enables consumers to
compute Mean Time To Recovery (MTTR) and close open alerts automatically" is
replaced by text to this effect: onset and recovery measure how long a
**condition** lasted and let consumers close alerts; the time to restore a
failed **asset** is the down interval declared with `asset.state` (Option B),
and a condition's recovery MUST NOT be presented as the asset's restoration.

# 8. Compatibility level of this change

**MINOR** under `GOVERNANCE.md` §4.1, for every part:

- a new event type -- consumers are already required to tolerate unknown
  `event_type` values (Option B);
- new optional fields (Option A, if chosen);
- clarifying text (`actual_duration_seconds`, *Recovery Events*).

Under §4.4, the correction in §7 adds a MUST NOT on presentation. It changes no
existing event and no producer's output; whether it constrains an existing
consumer is a question §4.4 asks the steward to answer in Review.

# 9. Effect on existing implementers

- **Producers:** nothing changes for any existing event. A producer that knows
  run/stop state MAY start emitting `asset.state`.
- **Consumers:** an unknown `event_type` is already tolerated, so nothing
  breaks. A consumer that today derives MTTR from onset-to-recovery keeps
  working and, after §7, stops labelling that number MTTR.
- **Libraries:** both SDKs gain a model class and its schema; the Node-RED and
  n8n packages MAY gain a node. `surface.json` decides whether the SDK profile
  requires the class; this memo proposes that it does, so a conforming SDK can
  produce every published type.
- **Reference scenarios:** the fixture is not changed. A second, separate
  scenario (a trip, its repair and the return to operation) is proposed for the
  implementation PR, so the five-event story every implementation already
  agrees on stays fixed.

# 10. What this memo does not decide

- Any formula for MTBF, MTTR, MTTRes, MRT or availability, and any threshold.
- Which states a given equipment class can have, or how a producer infers them.
- A curated published catalog for `detail` (`GOVERNANCE.md` §7: extending it
  needs no RFC; publishing values does).
- Partial work-order status updates, which `IAES_SPEC.md` lists as not yet
  supported.

# 11. Open questions

1. **Name.** `asset.state` or `asset.availability`? The first names what is
   declared; the second names one use of it.
2. **Unknown at start.** When a producer starts and does not know the previous
   state, does it emit its current state with a `reason` saying so, or stay
   silent until the first transition? The answer decides whether the first span
   of a series can be trusted.
3. **Reserve.** Table 4 places "reserve" under planned down time and "cold
   standby" under non-operating up time. Producers will confuse them; the
   guidance needs one sentence that tells them apart.
4. **Both options?** Is there a producer that can send completions with the down
   interval but cannot emit `asset.state` (a CMMS with no SCADA behind it)? If
   so, Option A's fields earn their place as a fallback, with a rule for which
   source wins when both exist.

# Author

Gilberto Garza, Wertek AI -- steward of IAES.
