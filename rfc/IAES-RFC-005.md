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

This memo proposes a new section of `GOVERNANCE.md` and moves two existing
files into the published release. It defines no wire format and changes no
schema.

**State: Review**, per `GOVERNANCE.md` §6, at the steward's request.
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

# Table of Contents

    1. What raised it
    2. Two classes, and why the first is not enough
    3. Who grants the profile
       3.1. Why it cannot be the steward
    4. What the profile requires
    5. What this standard cannot do about the name
    6. The steward's own SDK does not meet the profile
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

> **Wire conformance** is what *conforms to IAES* means with no qualifier. A
> system is wire-conformant when the events it produces validate against the
> published schemas and it observes the obligations the specification places on
> producers and consumers.

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

> **The IAES SDK profile** is a set of capabilities a library exposes. A library
> **may claim** the profile. Claiming it is a statement anyone can check against
> the published definition. Not claiming it is not a deficiency, and says
> nothing about whether the library is wire-conformant.

This is the distinction that keeps everything already built where it belongs. A
third party that emits correct events and exposes no `from_object` **is not
non-conformant to IAES**; it simply is not claiming the profile.
`iaes-opta-runtime` is the worked example: a deliberately narrow reference
runtime for a microcontroller, wire-conformant, and not an SDK. Under a single
class of conformance it would have to be described as deficient, which would be
false.

# 3. Who grants the profile

> **Nobody grants it. It is claimed and it is checkable.**
>
> A library claims the profile by stating which release's profile it meets. The
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

# 4. What the profile requires

The definition is `surface.json`, and `SDK_SURFACE.md` is its reasoning. This
memo does not restate the capability list; restating it would create a second
copy that drifts, which is the defect the file was written to end.

Three consequences follow, and they are the substance of this memo:

1. **`surface.json` stops being a draft.** Its `state` becomes `normative` for
   the profile, and it says which release's profile it defines.
2. **Both files enter the release manifest.** A definition that a claim is
   checked against must travel inside the object the claim names, or the claim
   names nothing. This is the point the measurement in §1 makes.
3. **The naming rule is part of the profile**, not a style note:

   > The same word, in each language's convention. Never a different verb.

   `compute_content_hash` and `computeContentHash` are one capability spelled by
   two languages. `from_dict` and `fromJSON` are two verbs, and a reader cannot
   tell whether they do the same thing without opening both.

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

# 6. The steward's own SDK does not meet the profile

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

This is published rather than worked around. The alternative — writing the
profile so that whatever the steward ships today happens to satisfy it — would
be a vendor-specific requirement in normative text wearing a general shape, and
§8 item 4 says those will not appear.

The gaps close before the release the profile is defined in, or the release
publishes the profile and the steward's own non-compliance with it. Both are
honest; the first is better; neither is a reason to weaken the definition.

# 7. Compatibility level of this change

**MINOR, derived under §4.5.**

```
R1  reduction?      No. No guarantee is withdrawn or conditioned. Wire
                    conformance is unchanged in scope and in meaning, and
                    nothing that conforms today stops conforming.
R2  classification  No. This memo states no rule about how future changes
    only?           are classified.
R3  addition?       Yes. It adds an obligation of the steward -- to publish
                    the profile definition inside every release that defines
                    one -- and reduces nothing.  ->  MINOR
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

- **Whether the capability list is right.** It is measured, not designed, and
  the shape of its gaps says where attention went rather than what an SDK needs.
  Revising which capabilities the profile requires is a change to
  `surface.json`, classified when it is proposed.
- **How a profile change is classified.** Once `surface.json` is normative,
  adding a required capability makes previously conforming libraries
  non-conforming to the profile. That is the shape §4.4 was written for, and it
  should be confirmed against §4.4 rather than assumed — in the memo that first
  proposes such a change, not here.
- **Anything about the wire.** No field, no schema, no obligation on any
  producer or consumer.

# 10. Proposed incorporation

1. **§2 and §3 of this memo as a new `GOVERNANCE.md` §9**, titled *Conformance*,
   defining the two classes and stating that the profile is claimed and checked
   rather than granted.
2. **`SDK_SURFACE.md` and `surface.json` added to the release manifest's
   normative set**, so the definition travels inside the release a claim names.
3. **`surface.json`'s `state` becomes `normative`**, naming the release whose
   profile it defines.

§1 through §8 of `GOVERNANCE.md` are unchanged.

# Author

G. Garza, Wertek AI, Inc. — steward of the Industrial Asset Event Standard.
