```
IAES                                                        G. Garza
Request for Comments: 008                                   Wertek AI
Category: Standards Track                            September 2026
ISSN: N/A

           The Mechanics of the Jump to IAES 2.0
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

**State: Accepted**, per `GOVERNANCE.md` §6.
**Compatibility: MAJOR. Target version: IAES 2.0.** Distribution is unlimited.

It stayed in Review until the release that carries it, because its decisions
were about schemas and text that did not exist yet and §6 defines Accepted as
incorporated. The 2.0 cut incorporated them, so it is Accepted here.

# Copyright Notice

Copyright (c) 2026 Wertek AI, Inc. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

`IAES-RFC-007` ratified what had accumulated since 1.4. This memo decides the
mechanics of the release itself: where the 2.0 schemas live, what a 1.x URI must
keep serving, what `spec_version` accepts, and what the migration statement §8
item 3 requires must say.

Most of it is `GOVERNANCE.md` §5 applied rather than invented. **One rule is
new**, and it is the one a release engineer can get wrong without noticing:

> A representation served under a major's URI MUST remain the representation of
> that published major, and MUST NOT be regenerated from a later release.

# Table of Contents

    1. What §5 already decides
    2. The rule §5 does not state
    3. The decisions
       3.1. Eight new identities
       3.2. What spec_version accepts
       3.3. How a 2.0 consumer reads a 1.4 event
       3.4. What is a canonical identity, and what is a copy
    4. The migration statement
    5. Copies are not drift
    6. What this memo does not decide
    7. Compatibility level of this change
    8. Effect on existing implementers
    9. Proposed incorporation

# 1. What §5 already decides

Three of the four things a reader would expect this memo to decide are already
decided, and repeating them as if they were new would be the mistake this
project has spent a fortnight learning to avoid:

> - **versioned by URI** — a MAJOR version publishes under a distinct path.
> - A published `$id` is **immutable**. Changing one is a MAJOR change.
> - (§8 item 1) Published versions are never edited in place, never unpublished,
>   and always resolvable at their URI and DOI.

So `/schema/v2/` is not a proposal. It is what §5 requires of any major, and
this memo applies it.

⚠️ **§5.1 does not apply and must not be reached for.** Its exception is for an
identifier that *never resolved*, on the stated ground that no implementer can
have depended on it. Every `/schema/v1/` URI resolves today and has since 1.4.

# 2. The rule §5 does not state

§5 says a published `$id` is immutable and §8 says a published version stays
resolvable. Between them they say the **address** must keep working. Neither
says what it must keep **returning**.

That gap has a specific failure mode, and it is not hypothetical — it is one
`cp` away on the day of the cut:

```
main/schema/*.schema.json   is v2 after the cut
        │
        └── materialised to  /schema/v1/*      ← v2 content under a v1 identity
```

Every URI resolves. Every check that asks *does it resolve?* passes. And a 1.x
consumer fetching its own schema receives a document from a major it was never
built for. **A `$id` whose address survives and whose content silently changes
is worse than one that 404s**, because the 404 is visible.

> **[WIRE]** A representation served under a major's schema URI MUST remain the
> representation of that published major, and MUST NOT be regenerated from a
> later release.

The practical consequence, stated so it cannot be read as advice: after 2.0,
`/schema/v1/*` is materialised from the **`spec-v1.4` release** and from nothing
else. `main` is never the source of a historical major.

# 3. The decisions

## 3.1. Eight new identities

> **[WIRE]** IAES 2.0 publishes its eight schemas with `$id` under
> `https://iaes.dev/schema/v2/`. The eight `https://iaes.dev/schema/v1/` URIs
> continue to resolve, permanently, to the schemas published by the 1.x line.

The v1 base is not reserved-and-empty the way a corrected typo would be (§5.1).
It stays **live**, serving 1.x, for as long as anything can still be reading a
1.x event — which §8 item 1 makes permanent, not 24 months.

## 3.2. What `spec_version` accepts

Measured: the published envelope constrains `spec_version` to `^1\.[0-9]+$`.
**An event declaring `2.0` fails validation against all eight published
schemas**, which is correct and is the reason a major needs its own line.

> **[WIRE]** The 2.0 envelope constrains `spec_version` to `^2\.[0-9]+$`. The
> 1.x envelope is unchanged and keeps `^1\.[0-9]+$`.

Each major's envelope accepts that major's versions and no others. The
alternative — an envelope that accepts both lines — would make `spec_version`
carry information no schema acts on, and would leave a 2.0 consumer silently
validating a 1.4 payload against 2.0 rules.

## 3.3. How a 2.0 consumer reads a 1.4 event

This is the question §3.2 raises and it deserves an answer rather than an
inference, because the naive reading is that 2.0 breaks §4's BACKWARD promise.

> **[TEXT]** A consumer validates an event against the schemas of the major the
> event declares. `spec_version` says which; `dataschema`, when present, names
> the exact schema.

A 2.0 consumer reads a 1.4 event by validating it against `/schema/v1/`, which
resolves permanently (§3.1). Nothing is lost, and this is why the immutability
rule in §2 is load-bearing rather than tidy: **the migration path depends on the
old URI still returning the old document.**

## 3.4. What is a canonical identity, and what is a copy

Today `iaes.dev` serves the schemas at two places, and they are identical
because only one major exists. When two exist, an unversioned path becomes
ambiguous — and an ambiguous path that looks canonical will end up in somebody's
`dataschema`.

> **[WIRE]** Only `https://iaes.dev/schema/v<major>/<event_type>` is a canonical
> schema identity. A copy served at any other path is a convenience and MUST NOT
> be used as the value of `dataschema`.

That leaves the site free to offer an unversioned download of the current major
without that copy acquiring an identity it should not have.

# 4. The migration statement

§8 item 3 requires a MAJOR release to state its migration. Ratified content, so
the cut does not have to invent it under time pressure:

1. **`spec_version` becomes `2.0`,** and 2.0 events validate against
   `/schema/v2/`. 1.x events keep validating against `/schema/v1/`.
2. **Timestamps must be RFC 3339,** not merely ISO 8601. `IAES-RFC-007` §3.2
   classifies this as the narrowing it is, and it is **the only 2.0 change that
   makes a previously permitted timestamp representation non-conforming** — the
   one migration item that can invalidate an event *solely because of a value
   already on the wire*, with no change in behaviour required to produce it.
   ⚠️ No schema enforces it in either direction — `format` is an annotation — so
   it will not surface as a validation failure. It is stated here precisely
   because nothing will catch it.
3. **The four packages move to `2.0.x` in lockstep** (§3.1). Their first two
   numbers are the specification they implement.
4. **`from_object` is the canonical constructor name.** `from_dict` and
   `fromJSON` keep working as deprecated aliases; nothing has to change on
   upgrade.
5. **`IAES-RFC-002` changes producer and consumer behaviour**, and travels in
   this same release. Its §9 obliges producers to stop substituting values for
   optional fields the caller did not supply, consumers not to read an absent
   optional field as a default, anyone rejecting an unlisted
   `measurement_type` to relax, and anyone quoting `iso_13374_status` as ISO
   vocabulary to stop.

   **None of that invalidates a 1.4 event.** Every event schema-valid under 1.4
   stays schema-valid, and a 1.4 producer that keeps substituting stays
   conforming to 1.4 — it simply cannot declare 2.0. That is the distinction
   this release depends on and it is worth restating here rather than leaving to
   the reader of two memos:

   > **Having to change code is not the same as the version being breaking.**

   Item 2 changes what an existing *value* may be. This item changes what an
   adopting implementation must *do*. They are different obligations and they
   are classified differently — MAJOR and MINOR — for that reason.

6. **Everything else in 2.0 is governance, provenance and annotation**, and
   requires nothing of any implementation.

# 5. Copies are not drift

Measured on 2026-09-08, and it settles a question that looked like a design
choice and is not:

| location | function | authority |
|---|---|---|
| `iaes/schema/` | the release's normative set | **source** |
| `iaes/npm/schemas/`, `iaes/src/iaes/schemas/` | SDK runtimes | none — byte-identical, guarded |
| `iaes.dev/schema/v<major>/` | the canonical URI, served | none — a representation of a release |

The three copies inside the standard's repository share a single blob: 8 of 8
have the same object hash, and `test_every_bundled_copy_is_byte_identical`
keeps them that way.

> **Historical duplication is not drift when each copy is an immutable
> representation of a different published release.**

The copy that bit this project before was mutable and had no owner: eight
schemas declaring `$id` under a host that never resolved. A frozen copy of
`spec-v1.4` served forever under `/schema/v1/` is the opposite of that. It is
preservation of identity, and §2 is what makes the difference checkable rather
than a matter of intent.

# 6. What this memo does not decide

- **How a representation is materialised.** Whether a workflow copies, generates
  or downloads is implementation, and does not belong in a standard. What is
  normative is the constraint in §2: it comes from that release and no other.
- **Where the check lives.** The guard that proves `iaes.dev` serves what it
  claims to represent belongs in the site's repository, because that is where
  the change that can break it happens, and because the standard must not
  depend on a consumer of it to be green. That is a decision about the
  repositories, not about IAES.
- **Whether `format` should be asserted.** A narrowing under §4.2, still open.
- **RFC-002's five decisions.** They are incorporated by the same cut and stay
  their own memo.

# 7. Compatibility level of this change

**MAJOR**, and derived rather than assumed: a consumer built for 1.x cannot
validate a 2.0 event, because the 2.0 envelope constrains `spec_version` to its
own line (§3.2). That is `GOVERNANCE.md` §3 exactly — a change that breaks the
compatibility guarantee defined in §4.

The release is MAJOR for this reason and for `IAES-RFC-007` §3.2's narrowing,
independently. §4.5's release rule makes it the maximum either way.

# 8. Effect on existing implementers

**A 1.x implementation that does nothing keeps working.** Its schemas resolve
permanently at their published URIs, its events stay valid, and §4.3 keeps 1.x
supported for at least 24 months — §8 item 1 keeps it resolvable beyond that.

**An implementation adopting 2.0** does everything in §4: declare `2.0`, point
at `/schema/v2/`, emit RFC 3339 timestamps, take the `2.0.x` packages, and adopt
the producer and consumer behaviour `IAES-RFC-002` requires.

Two of those are not the same kind of obligation, and the migration statement
separates them because a reader planning an upgrade needs the difference:

```
item 2   an existing VALUE stops conforming        no behaviour change needed
         to produce it -- the timestamp already
         written is the problem                    MAJOR

item 5   an implementation must BEHAVE differently no 1.4 event becomes
         to declare 2.0                            invalid                MINOR
```

# 9. Proposed incorporation

By the 2.0 cut, in one release:

1. **`GOVERNANCE.md` §5** gains §2's rule — a representation served under a
   major's URI stays that major's, and is never regenerated from a later
   release — and §3.4's statement of what is a canonical identity.
2. **The eight schemas** publish with `$id` under `/schema/v2/`, and the
   envelope's `spec_version` pattern becomes `^2\.[0-9]+$`.
3. **`IAES_SPEC.md`** carries the version history entry and the migration
   statement in §4.
4. **`surface.json`**'s `iaes_spec_version` becomes `2.0`, per the lockstep in
   §3.1.

This memo flips to Accepted in the same change, because that is the moment its
decisions become incorporated.

# Author

G. Garza, Wertek AI, Inc. — steward of the Industrial Asset Event Standard.
