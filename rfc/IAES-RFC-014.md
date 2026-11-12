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
analysed part by part in §7.
**Target version: none stated.** A target is stated by the steward when the
memo moves to Review; the next minor after 2.1 is the natural one.
Distribution is unlimited.

Numbered 014 because 009 is held by an open draft (the Appendix C memo,
wertek-ai/iaes#44) and 010 to 013 are taken.

# Copyright Notice

Copyright (c) 2026 Wertek AI. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

`asset.state` (`rfc/IAES-RFC-010.md`) can already say that an asset went down
unplanned, and its open `detail` field already carries `trip` and
`manual_shutdown` as examples. It cannot say, in a way two consumers read the
same, that the stop came from an **emergency stop** -- the most deliberate
stop an operator makes, and one a plant may want to count apart from a trip.

This memo proposes **no new field and no schema change**. It publishes two
values for `detail` -- `emergency_stop` and `emergency_switching_off` --
places both in the down-time family RFC-010 already uses for a trip and a
manual shutdown, and states a boundary: IAES reports that a stop happened; it
never triggers, resets, bypasses or commands a safety function.

# Table of Contents

    1. The problem
    2. The two values
    3. Where they sit on the timeline
    4. Optional and advisory
    5. The boundary: a record, never a command
    6. Worked example
    7. Compatibility level, part by part
    8. Effect on existing implementers
    9. Proposed incorporation
    10. What this memo does not decide, and future work
    11. Open questions
    Appendix A. Informative note on standards not consulted

# 1. The problem

Measured on `main` at `59765fe` (2026-11-12):

1. **`detail` is open and has no published values.** `IAES_SPEC.md`,
   *`asset.state` (v2.1)*, field table: "Anything finer: `trip`,
   `manual_shutdown`, `modification`, `reserve`, `testing`, … (examples, not a
   published catalog)". The schema says the same: "Open, and not a published
   catalog" (`schema/asset-state.schema.json`, `data.detail`). RFC-010 §12 left
   "a published catalog for `detail`" undecided, on purpose.
2. **So an emergency stop can have as many spellings as producers.** One SCADA
   could send `estop`, another `e_stop`, a third `emergency`, a fourth put it
   only in `reason`. Each is valid. A consumer that wants "how many emergency stops on
   this press this month" has to know every producer's spelling, and a second
   consumer with a different list reports a different number. That is the
   failure RFC-010 §1 describes for MTBF, one level finer.
3. **Two different acts can get one word.** "Emergency stop" can be used
   loosely both for stopping a hazardous movement and for cutting the electrical
   supply. They are different acts with different consequences for what has to happen before
   the machine runs again (§2). A free-text field will not keep them apart.

# 2. The two values

Both are values of `asset.state` `data.detail`. The definitions are this
memo's own words; no external text is quoted or relied on (Appendix A).

| Value | Meaning |
|---|---|
| `emergency_stop` | The asset was stopped on purpose by its **emergency stop device**, to halt a hazardous movement or process. The event records that the stop happened. It does not say why the device was operated, nor whether the stop performed as designed. |
| `emergency_switching_off` | The asset's **electrical supply was removed on purpose** by its emergency switching-off device. A different act from `emergency_stop`: there, the movement is stopped; here, the energy is removed. What has to be checked and restored before the asset runs again is different, and a consumer that counts one must not count the other under the same name. |

**Who uses them.** A producer that knows the down transition was caused by one
of these acts SHOULD use the matching value, rather than a spelling of its own.
A producer that cannot tell the two apart -- for example, one that sees only a
loss of motion -- SHOULD NOT guess: it sends the stop with no `detail`, or with
its own value, and says what it observed in `reason`.

**What they are not.** Neither value says anything about the safety function
itself: whether it was tested, certified, adequate, or bypassed. IAES carries
the fact that the asset stopped and by which act. Everything about the safety
function belongs to the system that implements it (§5).

# 3. Where they sit on the timeline

Both values go with:

```
state:      down
down_kind:  unplanned
down_cause: other_unplanned
```

This is the family RFC-010 already uses for a trip and a manual shutdown.
RFC-010 §2 cites ISO 14224:2016, Table 4, note d: a trip and a manual shutdown
are *other unplanned outages*, not corrective maintenance. An emergency stop is
a manual shutdown made through a particular device, so it takes the same
place. This memo cites ISO 14224 only through that citation in RFC-010 and adds
no reading of its own.

**An emergency stop is not, by itself, a failure.** It is an unplanned outage.
If the stop reveals that the item needs repair, the outage becomes corrective
maintenance, and that is a second `asset.state` event under RFC-010 §6 rule 1,
exactly as a trip that turns out to need repair. Whether a given emergency stop
counts towards an MTBF stays the consumer's classification, which the consumer
states (RFC-010 §3 and §6); with these values, it is made on a declared fact rather
than on a spelling.

**A boundary this memo draws, and asks the steward to confirm (§11 item 2).**
RFC-010 §2 notes that an item which cannot run because something *outside* it
is missing -- no feed, no power -- is not down by ISO 14224's definition, and
that 3.38 Note 3 counts that time as externally disabled **up** time
(`up_mode: externally_disabled`). `emergency_switching_off` is not that case:
the supply is removed **by the asset's own emergency switching-off device**, on
purpose, as a stop of that asset. A supply lost upstream for reasons outside the
asset -- a utility outage, a breaker elsewhere in the plant -- is externally
disabled time and does not use this value.

# 4. Optional and advisory

- **Not every asset is a machine.** A transformer, a tank or a building has no
  hazardous movement to stop. Nothing in this memo asks a producer to send
  either value, or to have an emergency stop to declare.
- **The field stays open.** `detail` remains a free string. Any other value
  stays valid, including the spellings producers use today.
- **Consumers.** A consumer MUST treat a `detail` value it does not recognise,
  and an absent `detail`, as *not classified* -- never as an error, and never as
  "not an emergency stop". This is the rule RFC-010 §6 already gives
  `down_cause` and `up_mode`, extended to `detail`. Absence asserts nothing, as
  `IAES_SPEC.md` *Producer Guidelines*, required behavior 3, already says of
  every optional field.
- **No SDK requirement.** The SDK profile (`GOVERNANCE.md` §9.2) is not changed
  by this memo (§7). An SDK MAY expose the two values as constants.

# 5. The boundary: a record, never a command

**IAES reports that a stop happened. It never triggers, resets, bypasses or
commands a safety function.**

The emergency stop function -- the device, its circuit, its reset, and the
decision that the machine may run again -- lives in the safety controller or
safety relay that implements it, which is designed, validated and maintained
for that purpose. An IAES producer reads that a stop happened, after it
happened, and declares it. An IAES consumer records it, counts it, shows it.

So this memo proposes, for `IAES_SPEC.md`:

> An `asset.state` event records that a stop happened. It is not a command.
> IAES defines no event that triggers, resets, bypasses or commands a safety
> function, and a consumer MUST NOT act on an IAES event as if it were one.

This is the stance IAES already takes for work orders: "A
`maintenance.work_order_intent` is a suggestion, not a command"
(`IAES_SPEC.md`, *Consumer Guidelines*, recommended behavior 6). It is stated again here, in
stronger words, because the cost of a misreading is not a wrong work order.

Two consequences, stated so they are not inferred:

- **Latency is not a property of this event.** `asset.state` is delivered when
  the transport delivers it. Nothing in IAES is fast enough, or meant, to take
  part in stopping anything.
- **Absence proves nothing.** No `emergency_stop` event does not mean no
  emergency stop: the producer may be down, or may not see the device. A
  consumer MUST NOT use the absence of these events as evidence that a machine
  is safe to operate.

# 6. Worked example

A press is running. At 10:02 an operator presses its emergency stop. At 10:09
the device is reset, the cause is cleared, and the press is restarted. No repair
is needed.

The events declare `spec_version` `2.2` as a placeholder for the release that
would carry this memo. The same bytes declaring `2.1` validate today; the value
simply has no published meaning there. The UUIDs are illustrative.

```json
[
  {"spec_version": "2.2", "event_type": "asset.state",
   "event_id": "3dbee145-2a2e-40e9-b42e-890b97810462", "correlation_id": "94572db2-3363-48da-bf75-cc9f969b8508",
   "timestamp": "2026-11-12T10:02:00Z", "source": "plant.scada",
   "asset": {"asset_id": "PRESS-201"},
   "data": {"state": "down", "down_kind": "unplanned", "down_cause": "other_unplanned",
            "previous_state": "up", "detail": "emergency_stop",
            "reason": "emergency stop button operated at the press"}},

  {"spec_version": "2.2", "event_type": "asset.state",
   "event_id": "d861b5a6-17c6-4851-ab76-d567f9701f8e", "correlation_id": "94572db2-3363-48da-bf75-cc9f969b8508",
   "source_event_id": "3dbee145-2a2e-40e9-b42e-890b97810462",
   "timestamp": "2026-11-12T10:09:00Z", "source": "plant.scada",
   "asset": {"asset_id": "PRESS-201"},
   "data": {"state": "up", "up_mode": "running", "previous_state": "down",
            "reason": "emergency stop reset; press restarted"}}
]
```

Any consumer gets the same facts:

- **7 minutes of unplanned down time** (10:02 to 10:09), cause
  `other_unplanned`, by emergency stop;
- **not a failure**: the cause never became `corrective_maintenance`, so a
  consumer that counts failures by declared cause does not count this one;
- one chain (RFC-010 §6 rule 7): the second event shares the first's
  `correlation_id` and points at it with `source_event_id`;
- no `content_hash` on either event (RFC-010 §6 rule 3), so a second
  emergency stop on the same press later that day is not mistaken for a
  duplicate.

The reset at 10:09 is not a separate event. The asset's state changed once
down and once up; the reset is how it came back, and `reason` says so. A
producer that cannot see the restart, only the reset, declares `up` when it
sees operation, as RFC-010 §6 rule 5 already says of a producer that cannot
tell a test run from a return to service.

# 7. Compatibility level, part by part

- **Publishing two values for an open field: MINOR**, `GOVERNANCE.md` §4.1
  ("Adding a value to an open catalog") and §7 (adding a value to a published
  catalog requires an RFC, which this is). `detail` stays an open string, so
  nothing that validates today stops validating. This is also the first time
  `detail` has any published value; RFC-010 §12 left that open, and §11 item 1
  asks whether other values should join at the same time.
- **The meaning of the two values**, `GOVERNANCE.md` §4.4:
  - **T1 (meaning).** No previous version stated a meaning for any `detail`
    value; they were examples. This memo *supplies* a meaning where the
    standard was silent, which §4.4 says is not changing one. T1 does not
    answer.
  - **T2 (cross-version).** A consumer that declares the release carrying this
    memo can still consume a 2.1 event with `detail: emergency_stop`, and
    reads it as 2.1 did -- an unclassified string -- unless the event declares
    the new release. **MINOR**; only implementations that declare that release
    adopt the meaning.
  - **Disclosed risk** (`GOVERNANCE.md` §8 item 2): a 2.1 producer may already
    send `emergency_stop` meaning something wider, such as any stop including
    loss of supply. That is a broken expectation, not a broken guarantee, and
    the release notes should say so.
- **The consumer rule in §4** (unknown or absent `detail` is *not classified*):
  a new consumer obligation, by §4.4. T1 does not answer -- no byte changes
  meaning. T2 answers yes. **MINOR**, for consumers that declare the release.
- **The boundary sentence in §5**, including its MUST NOT: a new consumer
  obligation, by §4.4. No previous version stated that an event could be acted
  on as a command; it is silent, and supplying a rule is not changing one. T2
  answers yes. **MINOR**, for consumers that declare the release.
- **No schema change.** The bytes at `https://iaes.dev/schema/v2/asset.state`
  do not change: within a major they never do (RFC-008, as restated in the
  reason for rejecting RFC-012). Adding the two values to the schema's
  `examples` would change those bytes, so it is **not** proposed for 2.x
  (§9).

# 8. Effect on existing implementers

- **Producers:** nothing changes for any existing event. A producer that knows
  an emergency stop or an emergency switching-off MAY start using the values
  today; once it declares the release carrying this memo, it SHOULD (§2). A
  producer that uses its own spelling stays valid.
- **Consumers:** unknown `detail` values are already tolerated, because the
  field is a free string. A consumer that declares the release treats them,
  and absence, as not classified, and does not act on any IAES event as a
  safety command.
- **SDKs:** no change required, and the SDK profile is unchanged. The schema
  copies in both SDKs stay byte-identical to the published schema.
- **Node-RED and n8n:** none. Producing `asset.state` truthfully still needs a
  flow that can set the envelope `timestamp`, as RFC-010 §10 already says.
- **Reference scenarios:** none required. An emergency-stop scenario would be
  informative and could follow the trip scenario RFC-010 §10 proposes.

# 9. Proposed incorporation

When Accepted, in the same change:

- `IAES_SPEC.md`, *`asset.state`*:
  - the `detail` row: "**Open.** Published values: `emergency_stop`,
    `emergency_switching_off` (below). Other values, such as `trip`,
    `manual_shutdown`, `modification`, `reserve` and `testing`, are examples,
    not published values";
  - a short paragraph *Emergency stops* with §2's two definitions, §3's
    placement and its boundary with externally disabled time, and §4's consumer
    rule;
  - the boundary of §5, in the words of its quotation;
  - the version history row.
- `conformance/`: a case where `detail: emergency_stop` validates, and one where
  an unknown `detail` validates.
- **Not changed in 2.x:** `schema/asset-state.schema.json` and its SDK copies
  (§7). Whether the `examples` annotation should list the published values is
  left to the next major, where the schema may change anyway.
- **Not added:** any reference to the standards named in Appendix A, in any
  normative artifact. They are not held, and `references/registry.json` would
  have to record them as unavailable before any normative text could name
  them.

# 10. What this memo does not decide, and future work

Not decided:

- What makes an emergency stop device adequate, how it must be wired, tested or
  reset, or which stop it must perform. That belongs to the system that
  implements it and to the standards that govern it, not to an event format.
- Any indicator built on these values, such as a count of emergency stops per
  month or a threshold for one.
- A published value for any other `detail` (§11 item 1).

Future work, mentioned so it is not proposed by accident:

- **`stop_category`**, an optional field with values `0` and `1`, for how the
  stop was made. Defining those values would need the standard that defines
  stop categories, which nobody working on this memo has opened (Appendix A).
  And adding a field to `asset.state` would change the schema's bytes, which
  waits for the next major (§7). Not proposed.
- **A `safety.*` event type**, for safety-relevant facts that are not a change
  of state: a guard opened, or a light curtain interrupted, while the asset was
  not running. A new event type at a new URI can be MINOR (`GOVERNANCE.md`
  §4.1), but what it should carry, and how it keeps §5's boundary, needs its
  own memo.

# 11. Open questions

1. **Only these two?** Publishing two values makes `detail` a field with
   published values for the first time. Should `trip` and `manual_shutdown`,
   which RFC-010 already uses and places under note d, be published at the same
   time, so that the catalog does not start lopsided? This memo does not
   propose it, to stay within the direction it was written for.
2. **The line between `emergency_switching_off` and externally disabled time**
   (§3). Is "removed by the asset's own emergency switching-off device" the
   right test, and is it one a SCADA can actually apply?
3. **Where the boundary of §5 lives.** In `IAES_SPEC.md` only, as proposed, or
   also as a commitment in `GOVERNANCE.md` §1, next to "no asset hierarchy, no
   equipment catalog, no commercial terms"? The second is a new obligation of
   the steward and would be classified under `GOVERNANCE.md` §4.5 R3.

# Appendix A. Informative note on standards not consulted

> **Informative, not normative, not verified against the text.** ISO 13850 is
> the international standard for the emergency stop function; IEC 60204-1 for
> its electrical implementation.

Neither document is held by the steward, and nobody working on this memo has
opened either. This memo claims no alignment with them, quotes nothing from
them, and cites no clause of them. The definitions in §2 are its own words,
written to keep two acts apart that plants already tell apart; they are not
offered as a reading of either standard. A reader who holds those standards is
invited to say, in this memo's pull request, where the definitions in §2 would
mislead.

# Author

Gilberto Garza, Wertek AI -- steward of IAES.
