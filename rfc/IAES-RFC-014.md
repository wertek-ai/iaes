```
IAES                                                        G. Garza
Request for Comments: 014                                   Wertek AI
Category: Standards Track                             November 2026
ISSN: N/A

        Declaring an Emergency Stop: Two Published Values for
                       asset.state detail
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

**State: Draft**, per `GOVERNANCE.md` §6. It lives in its pull request and is
not merged to the default branch until it moves to Review or is closed
(`rfc/IAES-RFC-013.md`).
**Compatibility, as proposed: MINOR** under `GOVERNANCE.md` §4.1 and §4.4,
analysed part by part in §8.
**Target version: none stated.** A target is stated by the steward when the
memo moves to Review; the next minor after 2.1 is the natural one.
Distribution is unlimited.

Numbered 014 because 009 is held by an open draft (the Appendix C memo,
wertek-ai/iaes#44) and 010 to 013 are taken.

**Revised 2026-11-12** after an adversarial review of the first draft
(`dc3df52`). The changes:

- The safety boundary now forbids using IAES events, their contents **or their
  absence** to trigger, reset, acknowledge, bypass or authorize a safety
  function or a restart, or as a safety permissive, for events of any version
  (§5). Every safety obligation is incorporated, not only a quotation, and the
  memo says that validating events cannot show compliance (§10).
- The values are **producer declarations**, not established facts. Device
  activation, the asset's declared transition and the interruption of the
  electrical supply are separated, and neither value establishes that a safety
  function performed, that anything was isolated, or that hazardous energy is
  absent (§2).
- The placement on the timeline is **conditional** on an actual transition into
  an unplanned outage, with cases for a maintenance test, an asset already down,
  idle or standby, and a fault-triggered stop (§3).
- "Not a failure" becomes "does not establish a failure" (§3, §6).
- The test for `emergency_switching_off` is a **documented asset boundary**,
  not "the asset's own device"; unknown topology means the value is not used
  (§3).
- A multi-asset example: one button, a line of assets (§7).
- The counting claim is narrowed: these values mark qualifying outage
  declarations, not a complete log of activations or resets (§4).
- The numeric stop-category idea and the scope sentence about the external
  standards are removed (§11, Appendix A).
- The event-version gate is incorporated, with a mixed-version case (§9, §10).

**Revised again 2026-11-12** after a verification pass on `1858a7c`:
`emergency_switching_off` needs the same causal evidence as `emergency_stop`; the
asset boundary it depends on is defined, with the reason an interruption inside
it is the asset's down time; a fault-response stop may be declared
`corrective_maintenance` directly; in the line example the jammed feeder is
taken down by the jam, not the button; the abstract admits the planned test.

# Copyright Notice

Copyright (c) 2026 Wertek AI. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

`asset.state` (`rfc/IAES-RFC-010.md`) can already declare that an asset went
down unplanned, and its open `detail` field already carries `trip` and
`manual_shutdown` as examples. It cannot declare, in a way two consumers read
the same, that the outage was caused by operating an **emergency stop**
device, or by an **emergency switching-off** of the asset's electrical supply.

This memo proposes **no new field and no schema change**. It publishes two
values for `detail`, says when a producer may use them, places them on the
RFC-010 timeline only when the act actually took the asset down -- as an
unplanned outage in the ordinary case, or a planned one for an authorized test
(§3) -- and states a boundary: IAES events, their contents and their absence
are never an input to a safety function or to a decision to restart.

# Table of Contents

    1. The problem
    2. The two values, as producer declarations
    3. Where they sit on the timeline
    4. What the values can and cannot be used for
    5. The boundary: never a safety input
    6. Worked example: one asset
    7. Worked example: one button, a line of assets
    8. Compatibility level, part by part
    9. Effect on existing implementers, and the version gate
    10. Proposed incorporation
    11. What this memo does not decide, and future work
    12. Open questions
    Appendix A. Standards not consulted

# 1. The problem

Measured on `main` at `59765fe` (2026-11-12):

1. **`detail` is open and has no published values.** `IAES_SPEC.md`,
   *`asset.state` (v2.1)*, field table: "Anything finer: `trip`,
   `manual_shutdown`, `modification`, `reserve`, `testing`, … (examples, not a
   published catalog)". The schema says the same: "Open, and not a published
   catalog" (`schema/asset-state.schema.json`, `data.detail`). RFC-010 §12 left
   "a published catalog for `detail`" undecided, on purpose.
2. **So an outage caused by an emergency stop can be spelled as many ways as
   there are producers.** One SCADA could send `estop`, another `e_stop`, a
   third `emergency`, a fourth put it only in `reason`. Each is valid. A
   consumer that wants the outages of a press that were declared as caused by
   its emergency stop has to know every producer's spelling, and a second
   consumer with a different list gets a different answer.
3. **Two different acts can get one word.** "Emergency stop" can be used
   loosely both for operating a device that stops a hazardous movement and for
   switching off a machine's electrical supply. A free-text field will not keep
   them apart.

# 2. The two values, as producer declarations

Both are values of `asset.state` `data.detail`. Like everything in an IAES
event, they are **declarations by the producer**: what the producer states,
from the evidence it has. They are not established facts about the plant.

**Three observations, kept apart.** An emergency stop involves three different
observations, and a producer may have evidence of one and not the others:

| Observation | Example of evidence a producer may have | Carried by |
|---|---|---|
| **A. Device activation** -- the emergency stop or emergency switching-off device was operated | a status signal from the device or from the system that monitors it; an operator's record | not by `asset.state` on its own (§4) |
| **B. The asset's transition** -- the asset became unable to perform as required | the producer's usual evidence for `state: down` (RFC-010 §3: how a producer infers a state is its own business) | `state`, `down_kind`, `down_cause` |
| **C. Supply interruption** -- the asset's electrical supply was interrupted | a supply-status signal, a contactor or breaker feedback | not carried as a separate fact |

**The values.**

| Value | A producer declares it when |
|---|---|
| `emergency_stop` | it declares a **down transition (B)** of the asset **and** has evidence that an **emergency stop device was activated (A)** and that the transition followed from that activation. |
| `emergency_switching_off` | it declares a **down transition (B)** **and** has evidence that an **emergency switching-off device was activated (A)** and that the transition followed from that activation, **and** the device lies within this asset's documented boundary (§3). |

**What neither value establishes.** Neither establishes that a safety function
performed as designed, that the asset or any part of it was isolated, that its
electrical supply was actually removed, or that hazardous energy of any kind --
electrical, stored, mechanical, pneumatic, hydraulic, thermal -- is absent.
Neither establishes who operated the device or why: `source` identifies the
system that reports, not the person who acted, and `reason` is free text. Nor
does either establish a root cause.

**Activation without a declared transition.** If a producer has evidence of A
but not of B -- it sees the device operated and cannot tell what the asset did
-- it does **not** use these values to assert a stop. `asset.state` declares
transitions; it is not an activation log (§4).

**When the producer cannot tell which.** A producer that sees an outage but
cannot tell an emergency stop from an emergency switching-off, or from any
other stop, does not choose one. It declares the transition with no `detail`,
or with a value of its own, and says what it observed in `reason`.

**Using `reason` honestly.** A producer SHOULD use `reason` to say what its
declaration rests on and any timing limitation it knows of -- for example, that
the state is inferred from motion sampled every few seconds. This adds no
field; it uses the one RFC-010 already provides.

# 3. Where they sit on the timeline

**The ordinary case.** When the activation takes an asset that was **up** into
an outage that was **not planned**, the producer declares:

```
state:      down
down_kind:  unplanned
down_cause: other_unplanned
detail:     emergency_stop | emergency_switching_off
```

RFC-010 §2, citing ISO 14224:2016 Table 4 note d, places a trip and a manual
shutdown under *other unplanned outages*, not corrective maintenance. This memo
does **not** claim that the citation decides the case of an emergency stop: it
proposes, as its own judgment, that the ordinary case belongs in the same
place, because it is a deliberate unplanned stop that is not, by itself, a
repair. ISO 14224 is cited only through RFC-010, with no reading of its own.

**The cases that are not ordinary.** The `detail` value describes the act; the
cause stays what the producer would declare under RFC-010 anyway.

| Case | What the producer declares |
|---|---|
| **The asset is already down** (planned maintenance, corrective maintenance, another outage) and the device is operated | **No new event** if `state`, `down_kind`, `down_cause` and `up_mode` do not change: a change of `detail` alone is not a transition (`IAES_SPEC.md`, *`asset.state`*, rule 1). The existing classification stands. |
| **An authorized test of the device during a planned activity**, with the asset up | A planned outage, if the producer knows it was planned: `down_kind: planned`, `down_cause: other_planned`, with the `detail` value. |
| **The asset is up and idle or in standby** when the device is operated | The ordinary case **only if** the producer declares a transition: the asset is now unable to perform until the device is reset. A producer that cannot tell declares nothing. |
| **An automatic protective trip** -- no emergency device was operated | Not these values. RFC-010's `trip`. |
| **A person operates the device in response to a fault they saw**, and the activation is what takes the asset down | The `detail` value, with the cause the producer knows **at that moment**: `corrective_maintenance` directly if it already knows the item needs repair, otherwise `other_unplanned` and, when the need for repair becomes known, a second event with `corrective_maintenance` (RFC-010 §6 rule 1). A fault the producer can describe belongs in `asset.health`, not in `detail`. |
| **The fault itself took the asset down first**, and the device is operated afterwards | The first transition is declared from the fault, without these values (for example `trip`, or no `detail`). The later activation, with the asset already down, is the first row of this table: no new event. |
| **One device stops several assets** | Each asset is declared on its own, from that asset's own evidence (§7). |

**Emergency switching-off and externally disabled time.** RFC-010 §2 notes that
an item which cannot run because something outside it is missing -- no feed, no
power -- is not down by ISO 14224's definition, and that 3.38 Note 3 counts that
time as externally disabled **up** time (`up_mode: externally_disabled`). A loss
of supply could therefore be declared either way, and the producer needs a rule
it can apply.

**The asset boundary, for this rule.** The asset, plus the part of its
electrical supply that runs from an emergency switching-off device to the
asset, when the producer's configuration **documents** that this device exists
to switch off **this asset** as an emergency function. Whoever configures the
producer records that relationship; it is not inferred from where the device is
mounted or who owns it. Everything upstream of that device is outside the
boundary.

**Why an interruption inside the boundary is the asset's down time.** RFC-010's
externally disabled time is time when the asset cannot run because something
it needs from **outside** is missing. An emergency switching-off inside the
boundary is not that: it is an act on this asset, through a device that exists
to stop this asset, and the asset is unable to perform until that act is
undone. That is a deliberate stop of the asset, of the same kind as a manual
shutdown, not a missing external input. This is the memo's own judgment, not a
reading of ISO 14224 (§12 item 2 asks the steward to confirm it).

The rule proposed: a producer uses `emergency_switching_off` for an asset only
when the device that was activated lies **within that asset's documented
boundary** and the producer has evidence that the activation caused the down
transition.

- **Device within the documented boundary, activated, and the activation caused
  the transition** -- the ordinary case, with `emergency_switching_off`.
- **Supply lost upstream of the boundary, or with no documented device** -- a
  utility outage, a breaker elsewhere, a cause the producer cannot see -- the
  producer declares what RFC-010 already allows (for example `up` with
  `up_mode: externally_disabled`), never `emergency_switching_off`.
- **Boundary not documented, or topology unknown** -- the producer does not use
  the value.

§12 item 2 asks whether this rule is workable or the value should be deferred.

# 4. What the values can and cannot be used for

- **They mark qualifying outage declarations.** A consumer can select the
  down transitions a producer declared as caused by an emergency stop or an
  emergency switching-off, and the declared down time of those intervals.
- **They are not a complete log of activations or resets.** A second activation
  while the asset is already down produces no event (§3). A reset does not
  necessarily change the asset's state. One activation can produce several
  asset events (§7). So counting these events is counting **declared asset
  transitions**, not counting how many times a device was operated.
  Counting activations needs other evidence.
- **Optional and advisory.** Not every asset is a machine. Nothing here asks a
  producer to send either value.
- **The field stays open.** `detail` remains a free string; any other value,
  including the spellings producers use today, stays valid.
- **Consumers.** A consumer MUST treat a `detail` value it does not recognise,
  and an absent `detail`, as *not classified* -- never as an error, and never as
  "not an emergency stop". Absence asserts nothing (`IAES_SPEC.md`, *Producer
  Guidelines*, required behavior 3).
- **No SDK requirement.** The SDK profile (`GOVERNANCE.md` §9.2) is not changed
  (§8). An SDK MAY expose the two values as constants.

# 5. The boundary: never a safety input

**IAES events are records. They are never an input to a safety function or to
a decision that a machine may run.**

The emergency stop function -- the device, its circuit, its reset, and the
decision that the machine may run again -- lives in the safety controller or
safety relay that implements it. An IAES producer declares, after the fact,
what it observed. An IAES consumer records it, counts it, shows it, notifies
people about it.

So this memo proposes these consumer obligations. They apply to a consumer that
declares the release carrying this memo, **whatever version the event it is
processing declares**, and to **every** event type, not only `asset.state`:

1. A consumer MUST NOT use an IAES event, any of its contents, or the absence
   of an event, to trigger, reset, acknowledge, bypass or authorize a safety
   function.
2. A consumer MUST NOT use them to authorize, enable or permit a restart, or as
   a permissive in any safety-related decision. In particular, `state: up`, the
   end of a down interval, or a `reason` that mentions a reset is not
   permission to run.
3. A consumer MUST NOT treat the absence of an event -- of an `emergency_stop`,
   of any `down` -- as evidence that a machine is stopped, running, or safe to
   operate.

**What stays allowed.** Recording, counting, dashboards, analytics and
notifying people -- an alarm on a screen, a message to a supervisor -- are
ordinary uses. The line is not whether the consumer reacts; it is whether its
output takes part in a safety function or in permission to run.

This is the stance IAES already takes for work orders: "A
`maintenance.work_order_intent` is a suggestion, not a command"
(`IAES_SPEC.md`, *Consumer Guidelines*, recommended behavior 6). Here it is a
required behavior, because the cost of a misreading is not a wrong work order.

**Latency is not a property of these events.** They arrive when the transport
delivers them, after the act. Nothing in IAES is fast enough, or meant, to take
part in stopping anything.

# 6. Worked example: one asset

A press is running. At 10:02 an operator presses its emergency stop. At 10:09
the device is reset, the cause is cleared, and the press is restarted. No repair
is declared.

The producer, a SCADA, has a status signal from the emergency stop device (A)
and infers the press's state from its motion (B). The example assumes that
timeline is complete and its clock accurate.

The events declare `spec_version` `2.2` as a placeholder for the release that
would carry this memo. The UUIDs are illustrative.

```json
[
  {"spec_version": "2.2", "event_type": "asset.state",
   "event_id": "3dbee145-2a2e-40e9-b42e-890b97810462", "correlation_id": "94572db2-3363-48da-bf75-cc9f969b8508",
   "timestamp": "2026-11-12T10:02:00Z", "source": "plant.scada",
   "asset": {"asset_id": "PRESS-201"},
   "data": {"state": "down", "down_kind": "unplanned", "down_cause": "other_unplanned",
            "previous_state": "up", "detail": "emergency_stop",
            "reason": "e-stop status signal active; press motion stopped (motion sampled every 2 s)"}},

  {"spec_version": "2.2", "event_type": "asset.state",
   "event_id": "d861b5a6-17c6-4851-ab76-d567f9701f8e", "correlation_id": "94572db2-3363-48da-bf75-cc9f969b8508",
   "source_event_id": "3dbee145-2a2e-40e9-b42e-890b97810462",
   "timestamp": "2026-11-12T10:09:00Z", "source": "plant.scada",
   "asset": {"asset_id": "PRESS-201"},
   "data": {"state": "up", "up_mode": "running", "previous_state": "down",
            "reason": "press motion observed again after e-stop reset"}}
]
```

What any consumer can read, as declarations:

- **7 minutes of declared unplanned down time** (10:02 to 10:09), declared cause
  `other_unplanned`, declared as caused by an emergency stop. The timestamps are
  the instants the producer declares (RFC-010 §6 rule 2); the events do not show
  the producer's detection delay or clock accuracy, which is why `reason` states
  the sampling.
- **These events do not establish a failure.** The declared cause never became
  `corrective_maintenance`. A consumer whose stated policy counts failures by
  declared cause excludes this interval; a consumer with a different stated
  policy may not. The absence of a later `corrective_maintenance` does not prove
  that nothing failed.
- One chain (RFC-010 §6 rule 7); no `content_hash` (rule 3), so a second
  emergency stop on the same press later that day is not mistaken for a
  duplicate.
- **What the events do not say:** who pressed the button, why, whether the
  safety function performed as designed, and whether it was safe to restart.
  The restart at 10:09 was decided by people and the safety system, not by
  these events (§5).

# 7. Worked example: one button, a line of assets

A line has three machines on one emergency stop circuit -- **FEEDER-1**,
**PRESS-201** and **WRAPPER-3** -- and a **CONVEYOR-4** downstream that is not
on that circuit. At 10:02 an operator presses one emergency stop button because
FEEDER-1 is jamming. The producer's configuration documents which assets the
circuit stops.

| Asset | What the producer observes | What it declares |
|---|---|---|
| FEEDER-1 | stopped by the jam at 10:01, before the button: its own protection tripped | at **10:01**, from the jam: `down`, `unplanned`, `other_unplanned`, `detail: trip` (or `corrective_maintenance` directly if repair is already known). **Not** `emergency_stop`: the button did not cause this transition. At 10:02, already down: **no event** (§3) |
| PRESS-201 | on the circuit; running until 10:02, motion stopped with the button | at 10:02: `down`, `unplanned`, `other_unplanned`, `detail: emergency_stop` |
| WRAPPER-3 | on the circuit; running until 10:02, motion stopped with the button | at 10:02: `down`, `unplanned`, `other_unplanned`, `detail: emergency_stop` |
| CONVEYOR-4 | not on the circuit; running empty, then stopped by its own logic for lack of material | not `emergency_stop`. What RFC-010 already allows for a lack of feed, for example `up` with `up_mode: externally_disabled`, if the producer can tell |

- **Each asset is declared on its own**, with its own chain and its own
  `correlation_id` (RFC-010 §6 rule 7: one down interval is one chain, per
  asset). The producer does not copy one asset's classification to the others;
  each rests on that asset's own evidence and the documented circuit.
- **Two outages declared as emergency stops, one button press.** PRESS-201
  and WRAPPER-3 each carry `emergency_stop`, because the button took each of
  them down. A consumer that counts these events counts two declared outages.
  It cannot conclude that the button was pressed twice, nor that it was pressed
  once, from these events alone.
- **The asset that started it** is declared from its own cause. FEEDER-1 went
  down at 10:01 from the jam; the button found it already down, so it carries
  no `emergency_stop`. Had the producer's evidence been that the button stopped
  FEEDER-1 while it was still running, the value would apply to it too. Its
  fault, if the producer can describe it, belongs in `asset.health`.

# 8. Compatibility level, part by part

- **Publishing two values for an open field: MINOR**, `GOVERNANCE.md` §4.1
  ("Adding a value to an open catalog") and §7 (adding a value to a published
  catalog requires an RFC, which this is). `detail` stays an open string, so
  nothing that validates today stops validating. This is the first time
  `detail` has any published value; RFC-010 §12 left that open (§12 item 1).
- **The meaning of the two values**, `GOVERNANCE.md` §4.4:
  - **T1 (meaning).** No previous version stated a meaning for any `detail`
    value; they were examples. This memo *supplies* a meaning where the standard
    was silent, which §4.4 says is not changing one. T1 does not answer.
  - **T2 (cross-version).** A consumer that declares the release carrying this
    memo can still consume a 2.1 event with `detail: emergency_stop` with the
    meaning 2.1 gave it -- an unclassified string -- because the published
    meaning applies only to events that declare the new release (§9). **MINOR.**
  - **Disclosed risk** (`GOVERNANCE.md` §8 item 2): a 2.1 producer may already
    send `emergency_stop` meaning something wider. The version gate keeps that
    meaning from being reinterpreted; the release notes should still say so.
- **The consumer rule of §4** (unknown or absent `detail` is *not classified*):
  a new consumer obligation, §4.4. T1 does not answer -- no byte changes
  meaning. T2 answers yes. **MINOR**, for consumers that declare the release.
- **The safety obligations of §5**, which apply to events of every version: a
  new consumer obligation, §4.4. T1: no previous version stated that any event
  could be used as a safety input; it was silent, and supplying a rule is not
  changing one. T2: a consumer that declares the new release still consumes a
  2.0 or 2.1 event with the meaning that version gave it; it is only forbidden
  to use it as a safety input, which no version authorized. **MINOR**, adopted
  by consumers that declare the release.
- **No schema change.** The bytes at `https://iaes.dev/schema/v2/asset.state`
  do not change: within a major they never do (RFC-008, as restated in the
  reason for rejecting RFC-012; `IAES_SPEC.md`, version history, 2.0 row). That
  includes the `examples` annotation (§10).

# 9. Effect on existing implementers, and the version gate

**The version gate.** The published meaning of `emergency_stop` and
`emergency_switching_off` applies to an event that declares the release
carrying this memo, or a later one. In an event that declares an earlier
version, the same string is an unclassified `detail` value. A consumer MAY map
it to its own category by a private rule, and say so; it MUST NOT attribute the
IAES meaning to it.

**A mixed-version case.** A consumer that declares the new release receives, for
the same press, a 2.1 event with `detail: emergency_stop` at 08:15 and a 2.2
event with the same `detail` at 10:02. The 10:02 event is a declared emergency
stop in IAES's sense. The 08:15 event is an unclassified value. If the consumer
maps it with its own rule, its report says so rather than presenting both as
IAES-classified.

- **Producers:** nothing changes for any existing event. A producer MAY use the
  values when it declares the new release and meets §2; a producer with its own
  spelling stays valid.
- **Consumers:** unknown `detail` values are already tolerated. A consumer that
  declares the release applies the version gate, treats unknown or absent values
  as not classified, and observes §5 for every event it processes.
- **SDKs:** no change required; the profile is unchanged. The schema copies in
  both SDKs stay byte-identical to the published schema.
- **Node-RED and n8n:** none. Producing `asset.state` truthfully still needs a
  flow that can set the envelope `timestamp` (RFC-010 §10).
- **Reference scenarios:** none required.

# 10. Proposed incorporation

When Accepted, in the same change:

- `IAES_SPEC.md`, *Consumer Guidelines*, **Required behavior**: a new item, *Never
  a safety input*, carrying all three obligations of §5 and its "what stays
  allowed" paragraph, stated for every event type and every event version.
- `IAES_SPEC.md`, *`asset.state`*:
  - the `detail` row: "**Open.** Published values: `emergency_stop`,
    `emergency_switching_off` (below), for events that declare this release or a
    later one. Other values, such as `trip`, `manual_shutdown`, `modification`,
    `reserve` and `testing`, are examples, not published values";
  - a paragraph *Emergency stops* with §2 (the three observations, the two
    values, what neither establishes), §3 (the ordinary case, the table of other
    cases, the rule for `emergency_switching_off`), §4 (qualifying outage
    declarations, not an activation log) and the version gate of §9, with its
    mixed-version case;
  - a cross-reference to the new *Never a safety input* item;
  - the version history row.
- **Verification, said in the specification:** the §5 obligations are about what
  a consumer does with events, so **validating events cannot show compliance
  with them**. A reviewer checks it as a behaviour: *can any output of this
  consumer trigger, reset, acknowledge, bypass or authorize a safety function or
  a restart, or act as a safety permissive, on the basis of an IAES event, its
  contents or its absence?* If yes, the consumer does not conform.
- `conformance/`: a case where `detail: emergency_stop` validates and one where
  an unknown `detail` validates. These check only that the values are accepted,
  and the cases say so; they are not evidence about §5.
- **Not changed in 2.x:** `schema/asset-state.schema.json` and its SDK copies,
  including the `examples` annotation (§8). Whether it should list published
  values is left to the next major.
- **Not added:** any reference to the standards named in Appendix A, in any
  normative artifact. Before any normative text could cite them, the edition
  would first have to be identified and its availability declared in
  `references/registry.json`; and registering a document would still not show
  that it supports a claim, which needs the document opened.

# 11. What this memo does not decide, and future work

Not decided:

- What makes an emergency stop device or an emergency switching-off adequate,
  how either must be designed, wired, tested or reset. That belongs to the
  system that implements them and to the documents that govern them, not to an
  event format.
- Any indicator built on these values.
- A published value for any other `detail` (§12 item 1).

Future work, mentioned so it is not proposed by accident:

- **A record of device activations and resets**, separate from `asset.state`,
  for the counts §4 says these values cannot give: repeated activations while
  already down, resets, and activations that do not change an asset's state.
  It would be a new event type, and it would carry §5's boundary.
- **A `safety.*` event type** for safety-relevant observations that are not a
  change of state, such as a guard opened or a light curtain interrupted while
  the asset was not running. It needs its own memo.
- A field describing **how** a stop was performed was suggested and is not
  proposed: defining its values would depend on documents nobody working on
  this memo has consulted (Appendix A), and adding a field would change the
  schema, which waits for the next major (§8).

# 12. Open questions

1. **Only these two?** Publishing two values makes `detail` a field with
   published values for the first time. Should `trip` and `manual_shutdown`,
   which RFC-010 already uses, be published at the same time?
2. **Is the rule of §3 for `emergency_switching_off` workable, or should the
   value be deferred?** It rests on an asset boundary documented in the
   producer's configuration, and on the memo's own judgment that an
   interruption inside it is the asset's down time rather than externally
   disabled time. If integrators cannot record the boundary reliably, or the
   steward does not accept that judgment, publishing only `emergency_stop` now
   is the safer choice.
3. **Repeated activations and resets.** Should anything in 2.x let a producer
   declare a second activation while the asset is already down, or a reset that
   does not change the state, or does that wait for the activation record of
   §11?
4. **Where the boundary of §5 lives.** In `IAES_SPEC.md` only, as proposed, or
   also as a commitment in `GOVERNANCE.md` §1? The second is a new obligation
   of the steward, classified under `GOVERNANCE.md` §4.5 R3.

# Appendix A. Standards not consulted

> **Informative, not normative.** ISO 13850 and IEC 60204-1 are named here only
> so that a reader knows they exist. They were **not consulted**: the steward
> does not hold them and nobody working on this memo has opened them. **No
> alignment with either is claimed**, nothing is quoted from them, and no clause
> is cited.

The definitions in §2 describe what a producer declares and on what evidence;
they are not offered as a reading of either document, and their technical
adequacy is not established by having been written independently. A reader who
holds those documents is invited to say, in this memo's pull request, where §2
or §3 would mislead.

# Author

Gilberto Garza, Wertek AI -- steward of IAES.
