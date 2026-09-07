# IAES Governance

**Status:** Normative. Applies from IAES v1.4 onward, except §3's definition of
MAJOR, the pointer at the end of §4.2, §4.4, and item 2 of §8, which are
incorporated from `rfc/IAES-RFC-003.md` and apply from **IAES 2.0**.
**Last updated:** 2026-09-07

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

### 1.1 The boundary is checked, not remembered

> This section adds no commitment. It makes mechanical the one §1 already
> states, which is why it carries no RFC under §6.

Design Principle #1 is not self-enforcing. A dependency on the steward does not
look like the word "Wertek" in the text -- it looks like a default value, an
example payload, or an error message. In September 2026 this repository was
shipping our production API as the default endpoint of an n8n credential, our
namespace as the producer identity in the normative envelope schema, and our
multi-tenancy in a topic layout. All three passed every review, because a
reviewer reads prose and these were values.

So every repository that carries the IAES name runs
[`tools/check_frontier.py`](tools/check_frontier.py) in CI. It fails on three
things, in code and in code fences, and stays out of prose so that attribution,
stewardship and the changelog's record of what was removed remain sayable:

| | |
|---|---|
| **host** | infrastructure of the steward's as a value, default or placeholder |
| **namespace** | the steward's namespace taught as what a producer identity looks like |
| **model** | the steward's operating model as structure -- IAES carries no tenancy |

A route such as `/iaes/ingest` is deliberately not a violation: anyone can mount
it on their own server. The host in front of it is the dependency.

**Two things it does not check, stated rather than implied.** Prose that tells a
reader in words to point at the steward's host would pass; in practice the
configuration it describes lives in a source file, which is scanned. And
customer site names are not checked here, because recognising them needs a
customer list that does not belong in a public repository -- that check runs
before publishing, from the private side.


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
| **MAJOR** | Anything that breaks the compatibility guarantee defined in §4. | 1.x → 2.0 |

Every release is published with its own DOI. The **concept DOI** always resolves
to the latest version.

### 3.1 Package versions carry the specification they implement

The four published packages — `@iaes/sdk`, `node-red-contrib-iaes`,
`n8n-nodes-iaes` (npm) and `iaes` (PyPI) — version in **lockstep**, and their
number is read as:

```
     1  .  4  .  2
     ▲     ▲     ▲
     └─────┘     └── platform release: fixes and additions to the packages
     the SPECIFICATION they implement
```

**The first two numbers are the specification version.** A package numbered
`1.4.x` implements IAES 1.4. The third number counts releases of the packages
themselves, and moves without the specification moving.

Two consequences, and both are deliberate:

- A package cannot make a breaking API change without the specification
  advancing. These packages are wrappers around the standard; they have no
  independent life, and pretending otherwise is what produced four unrelated
  version numbers in the first place.
- All four move together, even when only one changed. A reader comparing two
  packages should never have to ask whether their numbers mean the same thing.

Build metadata after a `+` was considered for the platform counter and does not
work: SemVer §10 requires it to be **ignored in precedence**, so npm treats
`1.4.0+1` and `1.4.0+2` as the same version, and PEP 440 makes it a **local
version**, which PyPI refuses to accept. The third number carries it instead.

### 3.2 Every published package declares the family and the specification

Each package's README — the page a reader lands on at npm, PyPI or the Node-RED
Flow Library — **MUST** state:

1. **The four packages and how to install each one.** Somebody who finds the
   Python package has no way to learn the Node-RED nodes exist unless the page
   says so.
2. **The specification version it implements**, and that the first two numbers
   of the package version carry it (§3.1).

This is normative because it rots otherwise, and it did: at the time this rule
was written the SDK's page advertised **IAES v1.2**, two versions behind, and
two other pages advertised v1.3. A version claim on a package page is the first
thing an integrator reads and the last thing anybody remembers to update, so it
is checked by CI rather than by discipline.

## 3-bis. Two kinds of release

A **specification release** is the standard itself: the specification, this
document, the schemas and the accepted RFCs, published together under one tag.
It is indivisible, and it is what a DOI refers to.

An **implementation release** is a package. It declares which specification it
implements, and carries neither a specification nor a DOI of its own.

The two use separate tag namespaces, and the separation is enforced rather than
described: no tag can trigger both release workflows, and a specification tag
cannot reach the workflow that publishes packages.

| Kind | Tag shape | Example | Publishes |
|---|---|---|---|
| Specification | `spec-v<major>.<minor>` | `spec-v1.4` | nothing |
| Implementation | `<package>-v<major>.<minor>.<patch>` | `sdk-v1.4.1` | npm or PyPI |

The shapes differ as well as the prefixes: a specification version has two
components, an implementation version has three. That is two signals rather
than one, and a mistyped tag is rejected rather than acted on.

**The tag for IAES 1.4 is `spec-v1.4`.**

A specification tag verifies that every surface names the same version and
builds the release manifest. It does not create a release, and it publishes
nothing: minting the release, and with it the DOI, is a separate decision.

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

A change to a producer or consumer obligation that is **not otherwise
classified** by §4.1 or §4.2 is classified under §4.4.

### 4.3 Support window

A MAJOR version remains published and resolvable for **at least 24 months**
after its successor is released. Nothing is ever unpublished: a superseded
version stays retrievable at its own URI and DOI.

Deprecation is announced in the specification's version history and, where a
transport allows it, signalled with the `Deprecation` and `Sunset` HTTP header
fields (RFC 9745 and RFC 8594).

### 4.4 Changes to producer and consumer obligations

Apply §4.1 and §4.2 first. If the change is classified there, that
classification governs and this subsection does not apply.

A change to an obligation on a producer or a consumer that §4.1 and §4.2 do
**not** otherwise classify is classified by the two tests below, applied in
order. The first that answers, decides.

**T1 — MEANING.** Must the same bytes, valid under version *N*, now be
interpreted with a different meaning? If yes: **MAJOR**.

§4.2 already says this of a named field. T1 is the same rule for meaning a
version stated by other means -- what the *absence* of a field asserts, what a
combination of fields asserts.

Meaning is *changed* only where the previous version **stated** one. Where the
previous version was silent, the new version **supplies** a meaning, and
supplying is not changing: there was no rule to contradict.

Silence is not permission: a producer whose behaviour a version never addressed
was not authorised by it, and a first rule on the point is not the reversal of
one. Silence is not a guarantee either -- where the standard said nothing,
implementations may have assumed different things, and a consumer whose
assumption the new obligation contradicts may break. That is a broken
expectation, not a broken guarantee (§8, item 2), and such risks are disclosed
in the release notes.

**T2 — CROSS-VERSION INTEROPERABILITY.** Under the compatibility direction §4
promises, can a consumer that declares *N+1* still consume an event that
conforms to *N*, with the meaning *N* gave it? If no: **MAJOR**. If yes, the
obligation may be **MINOR**, provided only implementations that declare *N+1*
have to adopt the new behaviour.

T2 is asked in the promised direction only. §4 guarantees BACKWARD: a consumer
at *N* meeting an event from *N+1* is outside the guarantee, and requiring it
would classify every addition as breaking.

An obligation that only restates what the existing normative text already
required is **PATCH**, per §3.

> **The reasoning is not a substitute for the tests.** *The previous version
> did not forbid it* answers T1 and answers nothing else. T2 is still asked,
> and asked about events rather than about intentions: an obligation that
> leaves an *N* event unreadable, or readable differently, by an *N+1* consumer
> is MAJOR however silent *N* was.

The rationale, including the framings this criterion rejected, is in
`rfc/IAES-RFC-003.md`.

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

### 6.1 What an RFC is, and what it is not

**An RFC is the proposal and rationale for a change; it is not normative
authority.** When an RFC is Accepted, the accepted change is incorporated into
the **applicable normative artifact or artifacts**. Those incorporated
artifacts govern IAES from the release that carries the change.
The RFC remains the historical record of *why* the decision was made.

This rule is stated here, in a normative document, on purpose. It used to be
stated only inside an RFC and inside a contributing guide -- so a reader could
learn that RFCs are not authority only by believing an RFC, or by opening a
file that governs this repository rather than the standard. An independent
implementer, given the repository in September 2026, cited an RFC as authority
for a normative claim. That was not a careless reading: nothing they were
entitled to rely on said otherwise, and the table below said "Normative from
the release that carries it" of an Accepted RFC.

The chain runs one way:

    GOVERNANCE.md      (normative)  defines what authority an RFC has
        v
    rfc/*.md           (rationale)  records why a change was made
        v
    the normative artifacts, as released, contain what governs

An implementer needs the third row. The second explains it. The first says so.

The third row is deliberately not a list. Which artifacts are normative can
change -- `SDK_SURFACE.md`, for one, declares itself normative for
implementations though not for the wire -- and a rule that enumerates a set
that can grow becomes false the day it grows.


| State | Meaning |
|---|---|
| **Draft** | Written and open for comment. Anyone may open one. |
| **Review** | The steward has accepted it for consideration and stated a target version. |
| **Accepted** | The decision is accepted and its change has been incorporated into the applicable normative artifact or artifacts. The incorporated change is normative from the release that carries it; the RFC itself remains rationale. |
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
2. A MINOR release preserves the BACKWARD compatibility guarantee in §4.
   Behaviour a prior version did not specify is not guaranteed across
   versions. Known risks involving such behaviour are disclosed in the release
   notes.
3. A MAJOR release is announced in the version history, keeps its predecessor
   available for at least 24 months, and states the migration.
4. Vendor-specific requirements will not appear in normative text.
5. The CC BY 4.0 licence on every published version is irrevocable.

---

*IAES is published under CC BY 4.0. Questions and change proposals:
[github.com/wertek-ai/iaes](https://github.com/wertek-ai/iaes).*
