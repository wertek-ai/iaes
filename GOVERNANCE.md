# IAES Governance

**Status:** Normative. Applies from IAES v1.4 onward.
**Last updated:** 2026-09-03

This document defines who maintains the Industrial Asset Event Standard, how it
changes, and what implementers are entitled to rely on. It exists because a
specification without a stated change process is a document, not a standard.

---

## 1. Scope: what IAES is, and what it will never become

IAES defines **how an industrial asset event is expressed**: the envelope, the
event types, and the measurement vocabulary. Design Principle #1 is vendor
neutrality: *no dependency on any specific platform or system*.

Three boundaries follow from that, and they are commitments, not preferences:

1. **IAES does not define an asset hierarchy.** Organizations model hierarchies
   differently (ISO 14224, ISA-95, custom). The specification requires only
   enough context to identify the asset. This is stated in the specification
   itself and is not subject to change by a minor release.
2. **IAES does not define equipment catalogs.** Which measurement positions a
   motor should have, which devices belong at each position, and which
   thresholds apply are **implementation concerns**. A vendor may publish such a
   catalog; it does not belong in this specification.
3. **IAES contains no commercial terms.** No pricing, no billing units, no
   product capabilities. A standard with a price inside it stops being a
   standard.

**The test, in one sentence:** if a rule needs a specific vendor's catalog,
network, or judgment to be meaningful, it is not part of IAES.

## 2. Stewardship

IAES is authored and maintained by **Wertek AI**, which acts as its steward and
as the maintainer of its value catalogs (Appendix A failure modes,
`measurement_type`, `unit`).

The steward commits to:

- keeping the specification licensed **CC BY 4.0**, which is irrevocable for
  every version already published;
- keeping normative text free of vendor-specific requirements, per §1;
- responding to change proposals in public, in this repository;
- publishing every released version with a **permanent DOI**.

Wertek AI also maintains the **reference implementation**. Reference
implementations do not confer normative authority: where implementation and
specification disagree, **the specification governs**.

## 3. Versioning

IAES versions are `MAJOR.MINOR.PATCH`.

| Level | Meaning | Example |
|---|---|---|
| **PATCH** | Editorial only. No change to any schema. Typos, clarifications, examples, non-normative prose. | 1.3 → 1.3.1 |
| **MINOR** | Backward-compatible additions. New optional fields, new event types, new values in an open catalog. | 1.3 → 1.4 |
| **MAJOR** | Anything that can break an existing producer or consumer. | 1.x → 2.0 |

Every release is published with its own DOI. The **concept DOI** always resolves
to the latest version.

## 4. Compatibility policy

**Default mode: BACKWARD.** A consumer built for version *N* can read events
produced against version *N−1*. Practically: **consumers update first,
producers follow.** Implementers may rely on this.

### 4.1 Changes that are compatible (MINOR)

- Adding an **optional** field to an envelope or payload.
- Adding a **new event type**. Consumers are already required to tolerate
  unknown `event_type` values without erroring.
- Adding a value to an **open catalog** (for example a new `failure_mode`).
  Custom values are valid and consumers must tolerate them.
- Relaxing a constraint: widening a numeric range, making a required field
  optional, removing a pattern restriction.
- Adding, correcting, or clarifying non-normative text and examples.

### 4.2 Changes that are NOT compatible (MAJOR)

- Making an optional field **required**.
- Removing or renaming a field or an event type.
- **Narrowing** a constraint: closing an open string into an enumeration,
  tightening a numeric range, adding a pattern where none existed.
- Changing the meaning or the unit of an existing field while keeping its name.
- Changing the canonical `$id` of a schema (see §5).

> A worked example, because this is the case most likely to arise: turning
> `unit` from free text into a closed enumeration per `measurement_type` is a
> **narrowing** change. Payloads that validate today would stop validating. It
> is a MAJOR change and must be released as such, with the previous version
> kept available.

### 4.3 Support window

A MAJOR version remains published and resolvable for **at least 24 months**
after its successor is released. Nothing is ever unpublished: a superseded
version stays retrievable at its own URI and DOI.

Deprecation is announced in the specification's version history and, where a
transport allows it, signalled with the `Deprecation` and `Sunset` HTTP header
fields (RFC 9745 and RFC 8594).

## 5. Schema identity

Every JSON Schema carries a `$id` that is:

- **canonical** — one base URI for the project, and the schema is served at that
  exact address;
- **resolvable** — dereferencing it returns the schema;
- **versioned by URI** — a MAJOR version publishes under a distinct path.
  Following the CloudEvents rule: an incompatible change to a schema is
  reflected by a different URI.

A published `$id` is **immutable**. Changing one is a MAJOR change, because it
changes the canonical identity of the contract.

### 5.1 Narrow exception: an identity that never resolved

An `$id` that has **never been resolvable** was never a usable identity, and no
implementer can have depended on it. Correcting such an identifier is a **defect
correction**, released as MINOR, under all four of these conditions:

1. The old URI **never resolved** at any point after publication. Evidence of
   the failed resolution is recorded with the change.
2. The correction is announced in the version history, naming the old and the
   new URI.
3. The old URI is **reserved permanently** and never reassigned to a different
   schema.
4. The schema content is otherwise unchanged. A defect correction may not carry
   any other modification.

This exception exists because the alternative is worse: forcing a MAJOR release
for a typographical defect would spend an implementer's migration budget on
nothing, and would teach that version numbers do not mean what §3 says they
mean. It is deliberately narrow, and it does not apply to an identifier that
resolved and then stopped.

Producers should carry the schema URI in the event itself, so that a consumer
can tell what a message was written against without out-of-band agreement.

## 6. Change process

Changes are proposed as **RFCs** in `rfc/`, numbered sequentially.

| State | Meaning |
|---|---|
| **Draft** | Written and open for comment. Anyone may open one. |
| **Review** | The steward has accepted it for consideration and stated a target version. |
| **Accepted** | Merged into the specification. Normative from the release that carries it. |
| **Rejected** | Closed with a written reason. The reason stays in the repository. |
| **Superseded** | Replaced by a later RFC, which names it. |

An RFC states: the problem, the proposed change, the compatibility level per
§4, the effect on existing implementers, and at least one worked example.

Anyone may open an RFC. The steward decides, in public, and records the reason.

## 7. Value catalogs

`measurement_type`, `unit`, `failure_mode` and similar lists are **open
catalogs**: custom values are valid and consumers must tolerate them.

Extending a catalog does not require an RFC. Adding a value to the **published**
catalog does, so that the interoperability defaults stay curated rather than
accumulating whatever happened to appear in the field.

This mirrors the approach of ISO/TS 15143-3:2020, whose Annex E is normative and
defines a process for adding new data elements rather than forbidding extension.

## 8. What implementers can rely on

1. Published versions are never edited in place, never unpublished, and always
   resolvable at their URI and DOI.
2. A MINOR release will not break a working integration.
3. A MAJOR release is announced in the version history, keeps its predecessor
   available for at least 24 months, and states the migration.
4. Vendor-specific requirements will not appear in normative text.
5. The CC BY 4.0 licence on every published version is irrevocable.

---

*IAES is published under CC BY 4.0. Questions and change proposals:
[github.com/wertek-ai/iaes](https://github.com/wertek-ai/iaes).*
