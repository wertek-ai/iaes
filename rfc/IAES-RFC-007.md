```
IAES                                                        G. Garza
Request for Comments: 007                                   Wertek AI
Category: Standards Track                            September 2026
ISSN: N/A

  Ratifying Unreleased Normative Changes Accumulated After IAES 1.4
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

**State: Accepted**, per `GOVERNANCE.md` §6.
**Compatibility: MAJOR, and the reason is one change, not the set (§9). Target
version: IAES 2.0.** Distribution is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI, Inc. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

> Measured on 2026-09-08: `spec-v1.4 → main` contains normative changes that no
> Accepted RFC accounts for. **`main` is not a specification release**, so those
> changes have not become part of IAES. This memo decides whether they enter
> IAES 2.0, and records why.

**IAES 1.4 is untouched.** Nothing here corrects a published release; §8 item 1
forbids editing one in place and nothing here tries. What is being decided is
what the next release carries.

The changes are not one kind of thing. They are one **procedural** kind: work
that landed in the repository without the decision §6 requires before it can
reach a release. Each keeps its own classification.

# Table of Contents

    1. The measurement
    2. Why one memo, and why not RFC-002
    3. The changes, and how each is classified
       3.1. Two that must be corrected rather than ratified
       3.2. The one that is MAJOR
       3.3. The rest
    4. What the References section actually declares
    5. What this memo does not decide
    6. Compatibility level of this change
    7. Effect on existing implementers
    8. Proposed incorporation

# 1. The measurement

Taken before anything was written, against the published tag, over the set the
release manifest calls normative:

```
normative files    spec-v1.4: 10          main: 12
added              references/registry.json, surface.json
removed            none
modified           GOVERNANCE.md            +265 -5
                   IAES_SPEC.md              +90 -11
                   schema/iaes-envelope       +2 -2
                   schema/sensor-registration  +1 -1
```

Attribution, checked against every memo in `rfc/`:

| accounted for | by |
|---|---|
| `surface.json`; `GOVERNANCE` §4.4, §4.5, §9, the §3 MAJOR row, the §4.2 pointer, §8 item 2, §9.2 | RFC-003, RFC-004, RFC-005, RFC-006 |
| **everything else** | **nothing** |

# 2. Why one memo, and why not RFC-002

These changes are not semantically alike. A boundary guard, a citation
registry, a timestamp profile and two example strings have nothing in common as
subject matter.

What they have in common is **procedural**, and it is the only thing that
matters for whether they may enter a release: each is a normative change sitting
in `main` without the decision and rationale §6 requires. One memo can dispose
of that, once, with each change keeping its own classification.

**RFC-002 must not absorb them.** It has a stated problem, five decisions, and a
clear condition for moving from Review to Accepted. Adding governance,
references and historical drift to it would mix changes that are **already
incorporated** with decisions that are **not yet incorporated**, and the reader
of either would have to separate them again.

# 3. The changes, and how each is classified

## 3.1. Two that must be corrected rather than ratified

Two of the changes are not ratifiable as they stand, because each says something
that is no longer true.

**`GOVERNANCE.md` §1.1 contradicts itself, three paragraphs apart.** Its header
says:

> This section adds no commitment. It makes mechanical the one §1 already
> states, which is why it carries no RFC under §6.

And its body says:

> So **every repository that carries the IAES name runs
> `tools/check_frontier.py` in CI.**

That is an obligation of the steward, in normative text. §4.5 R3 classifies
adding or widening one as MINOR — so the section is not exempt from §6, it is a
MINOR change that was never recorded. The claim of exemption comes out and is
replaced:

> §1.1 does not widen the substantive boundary §1 states; it makes that boundary
> mechanically enforceable, and obliges the steward to enforce it. Its adoption
> is recorded by `rfc/IAES-RFC-007.md`.

**`GOVERNANCE.md` §6.1 cites an example that has since changed.** It says the
normative set can grow, and illustrates it:

> `SDK_SURFACE.md`, for one, declares itself normative for implementations
> though not for the wire

`SDK_SURFACE.md`'s first line today reads **"Status: not normative."** RFC-006
made `surface.json` the definition and left `SDK_SURFACE.md` as its reasoning,
precisely so there would not be two authorities over one thing. The example is
now false about its own repository.

The point §6.1 makes is right and the example is what broke. It is replaced with
`surface.json`, which is the artifact that actually joined the normative set —
and the replacement is worth making rather than deleting the example, because a
rule about a set that can grow reads better with an instance of it growing.

## 3.2. The one that is MAJOR

**ISO 8601 → RFC 3339**, in five places, one of which is a producer obligation:

```
1.4    Use ISO 8601 for timestamps. The `timestamp` field MUST be in UTC with
       timezone designator.
main   Use RFC 3339 for timestamps. The `timestamp` field MUST be in UTC with
       timezone designator. RFC 3339 is the profile JSON Schema's date-time
       refers to.
```

**This is a narrowing, and §4.2 classifies narrowing as MAJOR.** RFC 3339 is a
profile of ISO 8601: ordinal dates, week dates and some offset forms are valid
ISO 8601 and not valid RFC 3339. A producer emitting `2026-251T12:00:00Z` was
conforming under a literal reading of 1.4 and is not under this text.

It is not called a citation correction, and the distinction matters. Calling it
one would be classifying by the *shape* of the edit — a name swapped for a name
— rather than by what it does to what a producer may emit, which is the mistake
`GOVERNANCE.md` §4.5 R2's guard exists to prevent.

That the release is already MAJOR for other reasons does not make this free. It
makes it **cheap**, which is different: the migration statement §8 item 3
requires must mention it, because it is the only change here that can make a
previously conforming producer non-conforming.

⚠️ Measured, and it is why nobody has noticed: **the schemas never enforced
either.** `format: "date-time"` is an annotation in Draft 2020-12, so both SDKs
accept `timestamp: "banana"` today. The prose narrowed; the schema asserts
nothing in either direction. Making `format` binding is a separate narrowing and
is deliberately not in this memo.

## 3.3. The rest

| change | classification | why |
|---|---|---|
| `references/registry.json` joins the normative set | **MINOR · §4.5 R3** | adds a verifiable obligation about what IAES may cite; reduces nothing |
| §1.1 · the frontier guard | **MINOR · §4.5 R3** | an obligation of the steward, once §3.1's exemption claim is withdrawn |
| §6.1 · what an RFC is, and is not | **MINOR · §4.5 R3** | states where authority lives; adds no requirement on any implementation |
| ISO 13374 → "ISO 13374 series" (5 places) | **MINOR, steward's decision** | a normative annotation and a claim of provenance, which §4 still has no test for — the same class as RFC-002 decisions 1 to 3, and classified the same way for the same stated reason |
| 3 schema `description` strings | **MINOR, steward's decision** | same class: `ISO 8601` → `RFC 3339` in two, and `wertek.ai.diagnosis` → `acme.diagnostics` in one |
| `## References` (new section) | **split** — see §4 | the RFC 3339 rows inherit §3.2's MAJOR; the rest is provenance and disclosure, **MINOR, steward's decision** |
| examples: deployment-specific names → vendor-neutral names | **PATCH** | editorial companion edits; no rule changes |
| "reference implementations, none privileged" | **PATCH** | restates `GOVERNANCE.md` §2, which already says a reference implementation confers no normative authority |

The two `steward's decision` rows are marked that way rather than derived,
because §4 still has no test for a normative change that alters neither
representation, nor meaning, nor obligation. `IAES-RFC-002.md` §8.1.1 named that
gap and §4.5 deliberately did not close it — it closed the one above §4.4, not
the one below. Marking them honestly is better than inventing a derivation.

# 4. What the References section actually declares

The new `## References` section is the largest single change here — 58 lines —
and it would be easy to file as documentation. It is not.

It states, in the specification, that **an event can be schema-valid and not
IAES-conforming**:

> - **Normative for meaning** — must the value satisfy this document for the
>   event to conform to IAES?
> - **Enforced by the schema** — does the schema reject a value that does not?
>
> They are not the same question, and where they disagree the disagreement is
> the defect.

That is a statement about what conformance means, and it should be ratified
where a reader can find it, not slipped in as prose. It also publishes what the
schemas do **not** check — `format` for RFC 3339, RFC 4122 and RFC 3986;
membership for ISO 4217, where `^[A-Z]{3}$` admits `ZZZ` — which is a disclosure
about the standard's own limits and exactly the kind of thing a steward is
tempted to leave unsaid.

Ratified as: the RFC 3339 rows carry §3.2's MAJOR; everything else in the
section is **MINOR, steward's decision**, on the same ground as §3.3's
annotation rows.

# 5. What this memo does not decide

- **The mechanics of the 2.0 jump.** `$id` moving to `/schema/v2/`,
  `spec_version` accepting 2.0, `surface.json`'s `iaes_spec_version`, the
  version history entry and the migration statement §8 item 3 requires. Those
  changes do not exist yet; a memo that ratified them would be ratifying text
  nobody has written. They belong in their own memo.
- **RFC-002's five decisions.** Still Review, still not incorporated, and
  deliberately untouched here (§2).
- **Whether `format` should be asserted.** A narrowing under §4.2 with its own
  consequences for both SDKs.
- **Anything about a published release.** 1.4 stays exactly as published.

# 6. Compatibility level of this change

**MAJOR**, and the honest statement of why is that **one** change in the set is
MAJOR — the RFC 3339 narrowing in §3.2 — and `GOVERNANCE.md` §4.5 makes the
level of a release the maximum of the changes it carries.

Everything else here is MINOR or PATCH. Recording that distinction matters: a
reader of the migration statement needs to know that exactly one of these
changes can make a conforming producer non-conforming, and it is not the
governance work.

# 7. Effect on existing implementers

**One thing to check, and it is narrow.** A producer emitting a timestamp that
is valid ISO 8601 but not valid RFC 3339 — an ordinal date, a week date, an
offset form RFC 3339 does not admit — must move to an RFC 3339 form.

Measured: no schema rejects either form today, in either SDK, because `format`
is an annotation. So this will not surface as a validation failure. It is stated
here and belongs in the migration statement precisely because nothing will
enforce it.

Nothing else in this memo requires any implementation to change.

# 8. Proposed incorporation

1. **`GOVERNANCE.md` §1.1** — the exemption claim is replaced, per §3.1.
2. **`GOVERNANCE.md` §6.1** — the `SDK_SURFACE.md` example is replaced with
   `surface.json`, per §3.1.
3. **Everything else in §3.3 and §4 is ratified as it stands in `main`.** No
   text changes: this memo supplies the decision and the rationale that §6
   requires, which is what was missing.

# Author

G. Garza, Wertek AI, Inc. — steward of the Industrial Asset Event Standard.
