```
IAES                                                        G. Garza
Request for Comments: 002                                   Wertek AI
Category: Standards Track                            September 2026
ISSN: N/A

              IAES 1.5 Wire Contract Stabilization
```

# Status of This Memo

**State: Draft**, per `GOVERNANCE.md` §6. It is open for comment and has
not been accepted; nothing in it is in force, and no schema changes
until it is.

This document proposes the changes that constitute IAES 1.5. It is
Standards Track: it changes schema annotations and the obligations of a
conforming producer, and it changes no field, no type and no
enumeration value. Distribution of this memo is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI. This document is made available under
the Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

> **IAES 1.5 adds no new capability. It removes accidental constraints,
> ambiguous semantics, and unsupported external attributions before the
> IAES 1.x wire contract is frozen.**

Five defects were measured in the 1.4 artifacts. Each is a place where
the standard says something it cannot support, or fails to say something
it has already decided. None of them is discovered by reading; all five
were found by comparing one artifact against another.

This memo resolves those five and nothing else.

# Table of Contents

    1. Introduction
       1.1. Why this is the last widening
       1.2. What is deliberately not here
    2. Conventions
       2.1. What this memo can bind, and what it cannot
    3. Decision 1: severity is not priority
    4. Decision 2: iso_13374_status loses an attribution it cannot support
    5. Decision 3: condition_trend is IAES's own vocabulary
    6. Decision 4: an absent optional value is not an assertion
    7. Decision 5: an advisory list does not constrain the wire
    8. Compatibility
    9. Effect on existing implementers
    10. Worked example

# 1. Introduction

## 1.1. Why this is the last widening

`GOVERNANCE.md` §4 makes BACKWARD the default compatibility mode. What
it does not say is when the guarantee starts running in both directions.

IAES 1.5 is that point. After it, a minor release of 1.x may not remove
a constraint any more than it may add one, because a producer will have
been entitled to rely on both. Anything that requires breaking the wire
contract becomes 2.0.

That is why the five items below are worth a release of their own. Each
is a constraint or a claim that turned out to be accidental, and the
moment to remove an accidental constraint is before it is frozen, not
after.

## 1.2. What is deliberately not here

- **Asset relationship semantics.** `related_asset_id`, the naming of
  `parent_asset_id`, and the difference between a relationship and a
  hierarchy are a model question, not a constraint audit. They belong to
  a separate memo.
- **Reference provenance.** Which external documents IAES may cite, and
  on what evidence, is a governance question raised by §4 below. It is
  not resolved here.
- **Anything that adds a field, a type or a value.** IAES 1.5 removes
  and clarifies. A capability is not stabilization.

# 2. Conventions

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are to be
interpreted as described in BCP 14 (RFC 2119, RFC 8174) when, and only
when, they appear in all capitals.

Where this memo says a thing was *measured*, it means an artifact was
compared against another artifact on 2026-09-06, and the comparison is
reproducible from this repository.

## 2.1. What this memo can bind, and what it cannot

IAES is a wire contract. A memo of this standard may say what an event
means and what a conforming producer or consumer must do with it. It may
not say how anybody's library is built, and it has no authority over
Wertek's implementations that it does not equally have over a third
party's.

Every change below therefore carries one of three tags, and only the
first is binding on an implementer:

    [WIRE]  the schemas, and the obligations of a conforming producer or
            consumer. Binding on anyone who implements IAES.

    [TEXT]  the wording of this standard's own normative documents.
            Binding on this standard's publications, on nobody else.

    [REPO]  this repository's examples, SDKs and guards. Recorded so the
            evidence is reproducible. NOT normative for anyone, and in
            particular not for a third-party SDK: the surface an SDK
            offers is governed by SDK_SURFACE.md, which is explicitly
            normative for implementations and not for the wire.

A memo that quietly legislated for its author's own libraries would be
the standard depending on the steward, which GOVERNANCE.md §1 forbids.

# 3. Decision 1: severity is not priority

## 3.1. The problem

`IAES_SPEC.md` already says it, once:

    severity (on asset.health) describes the condition of the asset.
    priority (on maintenance.work_order_intent) describes the urgency
    of response.

That is correct and does not need inventing. It needs to exist where
implementers read.

Measured, it does not. The schemas — which are the normative artifacts,
and the only ones a validator runs — say:

    severity     "Severity classification"
    priority     "Suggested priority level"

Neither carries the distinction. A reader of the schema alone learns
nothing, and the confusion has already produced invalid published code:

    examples/alert_fatigue.py:162      priority="critical"
    examples/vibration_monitor.py:152  priority="critical"

`critical` is a **severity** value. The priority catalog is `low`,
`medium`, `high`, `emergency`. Both events are rejected by the
standard's own validator. They were published as examples.

`IAES_SPEC.md` also carries a table mapping the severity catalog onto
the priority columns of external systems. The table is not wrong, but it
is the bridge that invites the substitution: a reader sees `critical`
sitting under a column headed Priority.

## 3.2. The change

1. **[WIRE]** The `description` of `severity` in
   `asset-health.schema.json` MUST state that it describes the condition
   of the asset, and MUST state that it is not a priority.
2. **[WIRE]** The `description` of `priority` in
   `maintenance-work-order-intent.schema.json` MUST state that it
   describes the urgency of the proposed response, and MUST state that
   it is not a severity.
3. **[TEXT]** The mapping table MUST be labelled as a mapping *from*
   severity *to* each target system's own priority scale, so that it
   cannot be read as an equivalence between the two IAES catalogs.
4. **[REPO]** The two example programs are corrected to a value in the
   priority catalog. They were never valid; this is a repair, not a
   change to the standard.

**[WIRE]** A producer MUST NOT present a severity value in a priority
field, or the reverse. Which urgency an asset's condition deserves is
the consumer's judgment — it is the party that knows what else is
running — and IAES gives the two fields without deciding the mapping
between them.

# 4. Decision 2: iso_13374_status loses an attribution it cannot support

## 4.1. The problem

The field's description claims to carry the "ISO 13374-2 health status
level", and `IAES_SPEC.md` Appendix C presents the seven values as an
ISO mapping.

Measured: **ISO 13374-2 is not among the documents available to the
editor.** The claim cannot be verified, which means it cannot be
defended if an implementer or a certification body asks on what basis it
is made.

This is not a statement that the values are wrong. It is a statement
that the standard is asserting a correspondence it cannot show.

## 4.2. The change

1. **[WIRE]** The attribution to ISO 13374-2 MUST be withdrawn from the
   field's `description`. IAES 1.5 MUST NOT present this catalog as
   verified ISO vocabulary.
2. **[WIRE]** The seven values and the field itself are unchanged.
   Nothing that validates today stops validating.
3. **[WIRE]** The description MUST say that the values are IAES's own,
   and that any correspondence to an external standard is unverified.
4. **[TEXT]** Appendix C MUST carry the same withdrawal.
This memo does not state what ISO 13374-2 says, and MUST NOT be read as
doing so. The correct response to an unverifiable claim is to stop
making it, not to guess at what it should have been.

The attribution MAY be restored by a later memo, on evidence: the
edition consulted, the clause, and who verified it.

# 5. Decision 3: condition_trend is IAES's own vocabulary

## 5.1. The problem

`condition_trend` is documented as "Based on ISO 13374-4 §5.3
presentation states". Unlike Decision 2, that document **is** available,
so the claim was checkable. It was checked.

Measured against ISO 13374-4:2015 in full:

- §5.3 is titled *Information presentation (IP) module requirements*.
- The phrase "presentation states" does not occur.
- `improving`, one of the three published values, does not occur.
- `worsening` and `stable` occur as adjectives inside descriptions of
  health states, not as members of a trend enumeration.

So the three-value trend is IAES's own construct. That is a legitimate
thing for a standard to have. Presenting it as somebody else's is not.

## 5.2. The change

1. **[WIRE]** The field, its three values, its optionality and its
   nullability are **unchanged**. All three were measured to agree
   across the schema, the specification and both SDKs.
2. **[WIRE]** The attribution to ISO 13374-4 §5.3 MUST be withdrawn
   from the field's `description`.
3. **[WIRE]** The description MUST declare the catalog as IAES's own
   vocabulary.
4. **[TEXT]** `IAES_SPEC.md` MUST carry the same withdrawal.

Inventing a vocabulary is permitted. Declaring it as inherited is not.

# 6. Decision 4: an absent optional value is not an assertion

## 6.1. The problem

`anomaly_score` is constrained to `[0,1]`. The question this memo had to
answer was whether that range is meaning or accident, because after 1.5
the answer cannot be revisited within 1.x.

Measured, it is meaning. The field's own description reads "Probability
of anomaly (0 = normal, 1 = anomalous)", and it sits in a coherent
family: `health_index`, `anomaly_score` and `fault_confidence` are all
normalized to `[0,1]`. The range stays.

But the same measurement found the real defect, which is not the range.
An implementation was observed emitting `0.0` for `anomaly_score` and
`fault_confidence` whenever the producer supplied neither, while
correctly omitting every other optional neighbour. Under the field's own
published meaning, `0.0` asserts *definitely normal*. The producer said
nothing, and the event says something.

## 6.2. The change

The rule is general, and it is not about any one implementation:

> **[WIRE]** **An optional field that the producer did not supply MUST
> be omitted. An implementation MUST NOT substitute a value that carries
> meaning under the field's own definition.**

This applies to every optional field in every IAES event type, and it
applies with particular force to the normalized scores, where every
value in the range is a claim and none of them means "unknown".

Consumers MUST treat an absent optional field as *not asserted*, and
MUST NOT treat it as a neutral or default value.

# 7. Decision 5: an advisory list does not constrain the wire

## 7.1. The problem

The schemas close ten catalogs. The SDKs publish ten. Measured, they are
not the same ten, and they disagree in both directions — but only one of
the two directions is a defect of the standard.

- **`MeasurementType`** is published by both SDKs while the schema
  leaves `measurement_type` open. The SDK offers a list the wire never
  agreed to, and an implementation that rejects an unlisted value is
  stricter than the standard. **That is a wire question**: it decides
  what a conforming consumer may reject.

- **`triggered_by`** is closed in the schema since 1.0 and no SDK
  publishes a constant for it. This memo originally called that a
  producer with nowhere to read the values from. **That was wrong.** The
  schema publishes the five values, the schema is the normative
  artifact, and a producer reading it has everything it needs. What
  differs is the ergonomics of two particular libraries, which is
  governed by `SDK_SURFACE.md` and is **not** part of the wire contract.

The nine that pair agree value for value, in both languages.

## 7.2. The change

1. **[WIRE]** `measurement_type` remains **open**. A consumer MUST NOT
   reject an event because its `measurement_type` is not in any
   published list. No such list constrains the wire.
2. **[TEXT]** Any list of measurement types that this standard
   publishes MUST be labelled advisory, so that it cannot be mistaken
   for a constraint.
3. **[REPO]** `triggered_by` is added to this repository's SDKs as a
   convenience constant, and the asymmetry guard keeps the two sides
   declared. Neither binds a third-party implementation: an SDK that
   exposes no constants is still conforming, because conformance is
   measured on the wire.

# 8. Compatibility

**BACKWARD**, per `GOVERNANCE.md` §4.1. This is a MINOR release.

Nothing that validates under 1.4 stops validating under 1.5:

| change | effect on the wire |
|---|---|
| severity and priority descriptions | annotation only |
| ISO attributions withdrawn | annotation only; values unchanged |
| `condition_trend` declared IAES's own | annotation only; values unchanged |
| `anomaly_score` range | unchanged |
| absent-means-unasserted | producers emit fewer fields; all optional |
| `triggered_by` constant | this repository's SDKs only; no schema change |
| `measurement_type` advisory | documentation; the field was already open |

The one behaviour that changes is that a conforming producer stops
inventing values for optional fields. A consumer that depended on
`anomaly_score` always being present was relying on a field the schema
has always marked optional, and was not conforming.

# 9. Effect on existing implementers

- **Producers** MUST stop substituting values for optional fields the
  caller did not supply. Where an implementation currently defaults a
  normalized score to `0.0`, it MUST omit the field instead.
- **Consumers** MUST NOT read an absent optional field as a default.
- **Anyone quoting `iso_13374_status` as ISO vocabulary** MUST stop.
  The field continues to work; the claim about its provenance does not.
- **Anyone rejecting an unlisted `measurement_type`** is stricter than
  the standard and MUST relax. No published list constrains that field.
- **No SDK is obliged to expose any constant.** Conformance is measured
  on the wire, not on a library's surface.
- **No producer needs to change what it puts on the wire** to remain
  valid, with the single exception of the two example programs that emit
  a severity value in a priority field, which were never valid.

# 10. Worked example

An `asset.health` event from a producer that has a health index and a
severity, and has neither an anomaly score nor a fault confidence.

Before, as an implementation was observed to emit it:

```json
{
  "data": {
    "health_index": 0.42,
    "severity": "high",
    "anomaly_score": 0.0,
    "fault_confidence": 0.0
  }
}
```

The producer asserted nothing about anomaly, and the event says the
asset is definitely not anomalous and that there is no confidence in a
classification that was never made.

After:

```json
{
  "data": {
    "health_index": 0.42,
    "severity": "high"
  }
}
```

Both validate. Only the second is true.

# Author

    Gilberto Garza
    Wertek AI
    engineering@wertek.ai
