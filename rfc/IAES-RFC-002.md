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

This document proposes five wire-contract stabilization changes for
IAES 1.5. It is not the whole of that release: other memos carry the
fronts named in §1.2. It is
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

Five findings were measured in the 1.4 artifacts. Each is a place where
the standard says something it cannot support, fails to say something it
has already decided, or leaves a reader free to conclude the opposite of
what it means. Not all five are defects: one constraint turned out to be
correct, and what was wrong was the behaviour around it. None of them is
discovered by reading; all five were found by comparing one artifact
against another.

This memo resolves those five and nothing else.

# Table of Contents

    1. Introduction
       1.1. Why these five, and why now
       1.2. What is deliberately not here
    2. Conventions
       2.1. What this memo can bind, and what it cannot
    3. Decision 1: severity is not priority
    4. Decision 2: iso_13374_status loses an attribution it cannot support
    5. Decision 3: condition_trend is IAES's own vocabulary
    6. Decision 4: an absent optional value is not an assertion
    7. Decision 5: an advisory list does not constrain the wire
    8. Compatibility
       8.1. The principle exists; the operational criterion does not
       8.2. Does it clarify an obligation, or create one?
       8.3. Applying §3 directly
    9. Effect on existing implementers
    10. Worked example

# 1. Introduction

## 1.1. Why these five, and why now

`GOVERNANCE.md` §4 makes BACKWARD the default compatibility mode. What
it does not say is when the guarantee starts running in both directions
— when removing a constraint becomes as breaking as adding one, because
a producer has become entitled to rely on both.

Freezing the 1.x contract at that point has been proposed, and **this
memo does not enact it**: a rule binding every future 1.x release is a
change to `GOVERNANCE.md` and belongs to a memo of its own. What this
memo does is make the five changes that ought to precede such a freeze,
so that whatever is frozen is not an accident.

Each of the five is a constraint or a claim that turned out to be
unintended, and the moment to remove an unintended constraint is before
anyone is entitled to rely on it.

## 1.2. What is deliberately not here

- **Asset relationship semantics.** `related_asset_id`, the naming of
  `parent_asset_id`, and the difference between a relationship and a
  hierarchy are a model question, not a constraint audit. They belong to
  a separate memo.
- **Reference support.** Document identity and availability are now
  governed by `references/registry.json`: which document a citation means,
  and whether anyone can consult it. What remains unresolved is whether a
  cited document *supports* a particular attribution, which is relation-audit
  work and belongs to its own memo. §4 below turns on that distinction.
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

This memo is limited to the IAES wire contract. Within that limit it may
say what an event means and what a conforming producer or consumer must do
with it. It may not say how anybody's library is built, and it has no
authority over the steward's implementations that it does not equally have
over a third party's.

Whether IAES is *only* a wire contract is a larger question -- `GOVERNANCE.md`
already carries obligations about packages and their documentation -- and
this memo does not need to answer it to decide six fields.

Every change below therefore carries one of three tags, and only the
first is binding on an implementer:

    [WIRE]  the schemas, and the obligations of a conforming producer or
            consumer. Binding on anyone who implements IAES.

    [TEXT]  the wording of this standard's own normative documents.
            Binding on this standard's publications, on nobody else.

    [REPO]  this repository's examples, SDKs and guards. Recorded so the
            evidence is reproducible, and normative for nobody. Changes to
            this repository's SDK conveniences appear here only as
            consequences of the wire decision.

**This memo makes no claim about SDK-surface conformance.** Whether a second
class of conformance exists beside wire conformance, and who grants it, is an
open question of authority. A memo about six fields must not settle it in
passing.

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

**[WIRE]** `severity` MUST represent the condition of the asset.
`priority` MUST represent the urgency of the proposed response.

Stated as meaning rather than as provenance, on purpose. An earlier draft
said a producer must not present a severity value in a priority field — but
`low`, `medium` and `high` belong to both catalogs, and no consumer can tell
from the event whether `priority: "high"` was chosen as urgency or copied
across from severity. A rule the wire cannot observe is not a wire rule.

What is observable is caught already: `critical` is not in the priority
catalog, so the schema rejects it. The two example programs were invalid
before this memo and would be invalid without it.

Which urgency a condition deserves stays the consumer's judgment: it is the
party that knows what else is running, and IAES gives both fields without
deciding the mapping between them.

# 4. Decision 2: iso_13374_status loses an attribution it cannot support

## 4.1. The problem

The field's description claims to carry the "ISO 13374-2 health status
level", and `IAES_SPEC.md` Appendix C presents the seven values as an
ISO mapping.

Measured, in the order the standard now distinguishes: the citation
**does not identify a document** — it names a part but no edition, and ISO
revises under the same number — and separately, **no copy of the part is
held**. `references/registry.json` records it as `unresolved` for the first
reason, not `unavailable` for the second.

Either alone would make the claim undefendable if an implementer or a
certification body asked on what basis it is made. Together they mean the
question cannot even be posed.

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
  differs is the ergonomics of two particular libraries, which is **not**
  part of the wire contract. Which document governs that ergonomics is an
  open question this memo does not answer.

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
   declared. That follows from this repository's implementation choices and
   makes no claim about third-party SDK-surface conformance.

# 8. Compatibility

**Schema-wise, BACKWARD.** Nothing that validates under 1.4 stops validating:

| change | effect on the wire |
|---|---|
| severity and priority descriptions | annotation only |
| ISO attributions withdrawn | annotation only; values unchanged |
| `condition_trend` declared IAES's own | annotation only; values unchanged |
| `anomaly_score` range | unchanged |
| absent-means-unasserted | producers emit fewer fields; all optional |
| `measurement_type` advisory | documentation; the field was already open |

## 8.1. The principle exists; the operational criterion does not

Whether this release is MINOR turns on Decision 4, and the two halves of
`GOVERNANCE.md` answer differently.

§3 states the principle, and it is broad enough:

> **MAJOR** — Anything that can break an existing producer or consumer.

§4.2 is the criterion that operationalises it, and measured, its five entries
are all shaped like schema changes:

    making an optional field required
    removing or renaming a field or an event type
    narrowing a constraint
    changing the meaning or unit of an existing field
    changing a schema's canonical $id

So §3 asks the right question — *does this break a producer or a consumer?* —
and §4.2 does not say how to answer it for a change that touches no schema.
The gap is not a missing category. It is a missing test.

## 8.2. Does it clarify an obligation, or create one?

Measured against the specification as it stands: **it creates one.** Nothing in
IAES_SPEC.md says what the absence of an optional field means, and nothing
forbids a producer supplying a value it was not given.

But it is not a new direction. The Producer Guidelines already apply exactly
this principle to one field:

> A producer using a custom `event_type` with no published schema MUST omit
> the field rather than point at a URI that does not resolve.

That is *omit rather than fabricate*, decided once, for `dataschema`. Decision 4
generalises a rule the standard already made. The precedent settles the
direction; it does not settle the classification, which has to come from
governance.

## 8.3. Applying §3 directly

Absent the missing criterion, ask §3's question literally: what breaks?

A producer that declares 1.4 and writes `anomaly_score: 0.0` keeps working, and
a consumer that declares 1.5 keeps reading it. The bytes are unchanged and
`0.0` still means what it meant. Nothing that was valid becomes invalid, and no
existing meaning is reinterpreted.

What changes is narrower: an implementation that wants to *declare 1.5* must
stop substituting. That is a cost of adopting the new version, not a break of
the old one — and §4 already orients the guarantee that way: *consumers
update first, producers follow.*

The distinction worth stating, because it will recur:

> **"you must change code to implement a new version" is not the same as "the
> new version is breaking".** If it were, almost any new semantic requirement
> would force MAJOR, and MINOR could never carry an obligation.

The nearest counterexample, and why it holds: a 1.4 event that *omits*
`anomaly_score` could have been defaulted to `0.0` by a 1.4 consumer, and a 1.5
consumer must not. But absence had no stated meaning in 1.4 — a consumer that
defaulted was filling a gap, not following a rule — so this supplies a meaning
rather than changing one.

**On that reading Decision 4 is MINOR.** This memo does not assert it, because
the reading rests on a criterion `GOVERNANCE.md` does not yet contain. Writing
that criterion is a governance change and belongs in its own memo; until it
exists, this memo records the analysis and leaves the classification open.

# 9. Effect on existing implementers

- **Producers** MUST stop substituting values for optional fields the
  caller did not supply. Where an implementation currently defaults a
  normalized score to `0.0`, it MUST omit the field instead.
- **Consumers** MUST NOT read an absent optional field as a default.
- **Anyone quoting `iso_13374_status` as ISO vocabulary** MUST stop.
  The field continues to work; the claim about its provenance does not.
- **Anyone rejecting an unlisted `measurement_type`** is stricter than
  the standard and MUST relax. No published list constrains that field.
- **No event that is schema-valid under 1.4 becomes schema-invalid
  under 1.5.** Producers that synthesize meaningful values for absent
  optional fields must nevertheless change that behaviour to conform,
  and the two example programs that emit a severity value in a priority
  field were never valid to begin with.

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

Both validate. Only the second faithfully represents what the producer
supplied.

`0.0` is not a wrong value — it is the right one for an asset that was
measured and found unremarkable. What the first event gets wrong is
saying it on behalf of a producer that said nothing.

# Author

    Gilberto Garza
    Wertek AI
    engineering@wertek.ai
