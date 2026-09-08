```
IAES                                                        G. Garza
Request for Comments: 005                                   Wertek AI
Category: Process                                    September 2026
ISSN: N/A

        Two Classes of Conformance, and Who May Grant Them
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

This memo proposes a new section of `GOVERNANCE.md`. It defines no wire format,
changes no schema, and adopts no SDK profile.

**State: Accepted**, per `GOVERNANCE.md` §6.
**Compatibility: MINOR, derived under §4.5 (R3). Target version: IAES 2.0.**
Distribution is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI, Inc. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

IAES already implies a second normative surface — a description of what a
library must offer to call itself an IAES SDK — and has never defined its
authority, its conformance class, or how it enters a release.

This memo does not invent that surface. The table exists and is measured. It
answers the question the table has never had an answer to: **what right does it
have to require anything of anyone?**

Two classes: **wire conformance**, which is what conformance to IAES means
unqualified, and a claimable **SDK profile**, which a library may assert and
anyone may check. The steward does not grant the second, and §1 is the reason.

**This memo adopts no profile.** It defines the class and the rules a profile
must obey; deciding *which capabilities* one requires is a separate change with
its own memo, for the reason given in §4.

# Table of Contents

    1. What raised it
    2. Two classes, and why the first is not enough
    3. Who grants a profile
       3.1. Why it cannot be the steward
    4. What a profile requires — and why this memo does not say
    5. What this standard cannot do about the name
    6. What the steward's own SDKs look like today
    7. Compatibility level of this change
    8. Effect on existing implementers
    9. What this memo does not decide
    10. Proposed incorporation

# 1. What raised it

Three artifacts, measured on 2026-09-07, and they do not agree:

```
SDK_SURFACE.md    "Status: normative for implementations, not for the wire."
GOVERNANCE §6.1   names it -- "SDK_SURFACE.md, for one, declares itself
                  normative for implementations though not for the wire" --
                  while making the point that the normative set can grow
surface.json      "state": "draft"  AND  "normative_for": "implementations"
manifest          11 normative files: IAES_SPEC.md, GOVERNANCE.md,
                  references/registry.json, and the 8 schemas.
                  Neither SDK_SURFACE.md nor surface.json is among them.
```

So `GOVERNANCE.md` is **not silent** about it, which is more than *nobody
authorised this*. And at the same time nothing says what authority the document
has, what it would mean for a third party to comply, or how a file that calls
itself normative reaches the people it binds.

**A document that is normative and sits outside the published release is
normative in a way nobody can verify.** That is the defect, stated once.

# 2. Two classes, and why the first is not enough

> **Wire conformance** is what *conforms to IAES* means with no qualifier. An
> implementation is wire-conformant when each event it produces satisfies the
> applicable IAES validation rules — including envelope-only validation for a
> permitted custom `event_type` with no published payload schema — and it
> observes the producer or consumer obligations applicable to its role.

**The qualifier is load-bearing, and an earlier draft omitted it.** *Validates
against the published schemas* reads as complete and is not: the specification
permits a producer to emit an `event_type` in a namespace it controls and to
omit `dataschema`, since no schema is published for it. There the envelope is
what applies. This repository has already made that mistake once in code — a
validator that treated an unknown type as invalid — and writing it into the
definition of conformance would have promoted a fixed bug to a normative rule.

That is the whole of conformance today, and it should stay the whole of it. A
sensor gateway that emits correct events conforms to IAES. Nothing about its
internal API is any of this standard's business.

But wire conformance cannot answer the question `SDK_SURFACE.md` was written
for, because that question is not about events:

> An integrator who learns the Python SDK and moves to TypeScript looks for
> `validate` and does not find it, looks for `from_dict` and finds `fromJSON`.
> Nothing there is wrong on its own. Together they mean the SDKs have to be
> learned one at a time, which is the opposite of what a standard is for.

So a second class, and it is **claimable rather than imposed**:

> **An IAES SDK profile** is a set of capabilities a library exposes, adopted by
> a release and defined there. A library **may claim** a profile, naming the
> release whose profile it meets; the claim is a statement anyone can check
> against that release's definition. Not claiming one is not a deficiency, and
> says nothing about whether the library is wire-conformant.

This is the distinction that keeps everything already built where it belongs. A
third party that emits correct events and exposes no `from_object` **is not
non-conformant to IAES**; it simply is not claiming the profile.
`iaes-opta-runtime` is the worked example: a deliberately narrow reference
runtime for a microcontroller, wire-conformant, and not an SDK. Under a single
class of conformance it would have to be described as deficient, which would be
false.

# 3. Who grants a profile

> **Nobody grants it. It is claimed and it is checkable.**
>
> A library claims a profile by stating which release's profile it meets. The
> definition is published in that release, in machine-readable form. Any third
> party can check the claim without asking anyone, and the steward has no
> privileged role in the checking.

## 3.1. Why it cannot be the steward

`GOVERNANCE.md` §1 states the test in one sentence:

> if a rule needs a specific vendor's catalog, network, or **judgment** to be
> meaningful, it is not part of IAES.

A profile the steward granted would need the steward's judgment to be
meaningful. It would also make the steward the gatekeeper of a term its own
competitors need, which is the shape §1 exists to forbid — and the steward is a
vendor with SDKs in this market.

§2 already refuses the weaker version of the same thing: *reference
implementations do not confer normative authority; where implementation and
specification disagree, the specification governs.* A steward-granted profile
would reintroduce through certification exactly what §2 closed off through
implementation.

So the definition has to be **self-assessable**: published, versioned,
machine-readable, and checkable by someone who has never spoken to us.

# 4. What a profile requires — and why this memo does not say

An earlier draft of this memo did two things at once, and they were
incompatible.

It said, in §9, that it *does not decide whether the capability list is right —
it is measured, not designed*. And its incorporation made `surface.json`
normative and put it in the release manifest, which **is** deciding: a normative
`surface.json` is the definition of the profile, and its entries already say
`required: true`.

Prose that disclaims a decision does not undo an incorporation that makes it.
Had this shipped, *closing the matrix* would have stopped being implementation
work and become **implementing normative requirements nobody ever adopted** —
`validate` in the TypeScript SDK would have been mandatory because a measurement
was promoted, not because anyone judged it universal.

So this memo is authority only:

> **[TEXT]** A profile is adopted by a release, which carries its definition.
> This memo adopts none. `surface.json` stays a **draft measurement** and stays
> outside the normative set.

What the next memo has to decide, and this one deliberately does not:

- **Which capabilities are genuinely universal.** The list was measured across
  five implementations, and the shape of its gaps says where attention went, not
  what an SDK needs. `route` is already marked *not a gap* for libraries, which
  is a hint that the list is a starting point.
- **Whether a profile has levels.** A flow-runtime node package and a
  general-purpose library may not owe the same surface.
- **What `required: true` costs.** Each one makes some existing implementation
  non-conforming to the profile on the day it is adopted, including the
  steward's own (§6).

# 5. What this standard cannot do about the name

IAES is published under CC BY 4.0 and asserts no trademark. **This standard
cannot stop anyone from calling their library an IAES SDK**, and a memo that
pretended otherwise would be claiming an authority it does not have — the exact
failure this repository has spent a fortnight learning to catch.

What it can do is make the claim mean something: define the profile precisely,
publish the definition inside the release, and make it checkable by a third
party in an afternoon. A false claim then becomes a false claim about a
published, verifiable fact, rather than a difference of opinion.

That is weaker than certification and it is what a vendor-neutral standard is
entitled to.

# 6. What the steward's own SDKs look like today

Not a conformance finding: no profile is adopted, so nothing here is
non-conforming to anything. It is recorded because it is the fact most likely to
bend the next memo, and it should be visible before that memo is written rather
than discovered after.

Measured 2026-09-06 and unchanged at the time of writing:

| capability | `iaes` (Py) | `@iaes/sdk` (TS) | node-red | n8n | opta (C++) |
|---|:--:|:--:|:--:|:--:|:--:|
| `build` (7 types) | 7 | 7 | 3 | 6 | 2 |
| `from_object` | `from_dict` | `fromJSON` | — | — | — |
| `validate` | yes | **no** | yes | yes | — |
| `compute_content_hash` | yes | yes | n/a | n/a | yes |
| `schema_uri_for` | yes | yes | — | — | — |
| `route` | n/a | n/a | yes | — | — |
| `vocabulary` | 10 | 10 | 10 | 10 | 1 of 10 |

**`@iaes/sdk` cannot validate an event against its schema, and it is the SDK
both flow runtimes depend on.** Neither SDK uses the canonical name
`from_object`.

This is published rather than worked around, because the pressure runs in one
direction and it is worth naming in advance: **writing the profile so that
whatever the steward ships today happens to satisfy it** would be a
vendor-specific requirement in normative text wearing a general shape, and §8
item 4 says those will not appear.

When a profile is adopted, the gaps close before the release that adopts it, or
that release publishes the profile alongside the steward's own non-compliance
with it. Both are honest; the first is better; neither is a reason to weaken the
definition.

# 7. Compatibility level of this change

**MINOR, derived under §4.5.**

```
R1  reduction?      No. No guarantee is withdrawn or conditioned. Wire
                    conformance is unchanged in scope and in meaning, and
                    nothing that conforms today stops conforming.
R2  classification  No. This memo states no rule about how future changes
    only?           are classified.
R3  addition?       Yes. It adds a conformance class nobody is obliged to
                    claim, and one conditional obligation of the steward: a
                    release that adopts a profile carries its definition.
                    Reduces nothing.  ->  MINOR
```

This is the first memo in this series whose own level is **derived rather than
decided**. `IAES-RFC-003` had no rule and said so; `IAES-RFC-004` had one and
was forbidden from using it on itself. That §4.5 answers here, on the first
change that reaches it and is not itself, is the whole point of having written
it.

# 8. Effect on existing implementers

**No implementation has anything to do, and no reliance is reduced.**

A wire-conformant system stays wire-conformant, and the profile binds nobody who
does not claim it. What changes is that a claim which today means whatever the
claimant intends becomes a claim with a published definition behind it.

An implementer who wants the profile gains something they did not have: a way to
check, without asking the steward, whether their library qualifies.

# 9. What this memo does not decide

- **Which capabilities a profile requires**, and therefore whether the measured
  list in `surface.json` is the right one. §4 says why that is a separate
  decision rather than a detail of this one.
- **How a change to an adopted profile is classified.** Once a profile is
  normative, adding a required capability makes previously conforming libraries
  non-conforming to it. That is the shape §4.4 was written for, and it should be
  confirmed against §4.4 rather than assumed — in the memo that first proposes
  such a change.
- **Anything about the wire.** No field, no schema, no obligation on any
  producer or consumer.

# 10. Proposed incorporation

§2, §3 and §5 of this memo as a new `GOVERNANCE.md` §9, titled *Conformance*:
the two classes, the rule that a profile is claimed and checked rather than
granted, the rule that a release adopting a profile carries its definition, and
the limit on what the standard can do about the name.

**Nothing else.** `surface.json` stays a draft measurement, outside the
normative set, and the manifest is unchanged except for a comment recording
where an adopted profile's definition would go.

§1 through §8 of `GOVERNANCE.md` are unchanged.

# Author

G. Garza, Wertek AI, Inc. — steward of the Industrial Asset Event Standard.
