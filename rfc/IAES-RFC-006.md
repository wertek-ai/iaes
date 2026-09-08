```
IAES                                                        G. Garza
Request for Comments: 006                                   Wertek AI
Category: Standards Track                            September 2026
ISSN: N/A

              The IAES SDK Profile for IAES 2.0
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

This memo adopts the first IAES SDK profile, under the class `GOVERNANCE.md` §9
defines. It changes no schema and imposes nothing on the wire.

**State: Accepted**, per `GOVERNANCE.md` §6.
**Compatibility: MINOR, derived under §4.5 (R3). Target version: IAES 2.0.**
Distribution is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI, Inc. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

`IAES-RFC-005` created a class and deliberately adopted no profile, because
promoting a **measurement** to a normative definition would have decided by
accident which capabilities an SDK owes.

This memo decides it on purpose, and the decision is narrower than the
measurement. **The profile is for libraries.** Flow-runtime node packages are a
different artifact class and are out of scope. `route` is not required, because
a library caller uses a switch. Six capabilities are, and one of them the
steward's own TypeScript SDK does not have.

# Table of Contents

    1. What a profile is for, and what follows from that
    2. Scope: libraries, and why not the node packages
    3. The required set
       3.1. What is required, and what each one costs
       3.2. What is not required, and why
    4. Names
    5. Failure
    6. How a library claims the profile
    7. No levels in 2.0
    8. Compatibility level of this change
    9. Effect on existing implementers
    10. What this memo does not decide
    11. Proposed incorporation

# 1. What a profile is for, and what follows from that

`SDK_SURFACE.md` states the purpose in the sentence that raised the whole
question:

> An integrator who learns the Python SDK and moves to TypeScript looks for
> `validate` and does not find it, looks for `from_dict` and finds `fromJSON`.
> Together they mean the SDKs have to be learned one at a time, which is the
> opposite of what a standard is for.

So the profile exists to make **learning transfer between implementations**.
Everything below follows from that sentence, and where the measurement and the
purpose disagree, the purpose decides.

# 2. Scope: libraries, and why not the node packages

> **[TEXT]** The IAES SDK profile applies to a **library**: a package that
> exposes an API to code written by its user. A flow-runtime package — Node-RED
> nodes, n8n nodes — is a different artifact class and is out of scope.

The measured matrix has `n/a` cells in it, and they are not gaps. They are the
symptom of one table describing two kinds of thing:

```
route          n/a for libraries      a caller uses a switch
from_object    n/a for nodes          the message already IS an object
```

Nothing transfers between a palette and an API. An integrator who learns the
Node-RED nodes and then opens the Python SDK is not looking for the same words;
they are looking for a different kind of artifact. A profile that spanned both
would require of each what only the other can meaningfully offer, which is how
the matrix came to have cells that cannot be filled.

The node packages are still wire-conformant, still published, still supported,
and now explicitly **not deficient** for claiming no profile (§9.2 of
`GOVERNANCE.md`). If a flow-runtime profile is ever wanted, it is its own
adoption with its own memo.

# 3. The required set

## 3.1. What is required, and what each one costs

> **[TEXT]** A library claiming the IAES SDK profile of IAES 2.0 MUST expose all
> six:

| capability | what it is | why it is universal |
|---|---|---|
| `build` | construct an event of each of the **7 published types** | a library that cannot emit some standard type makes the type invisible to its users |
| `from_object` | construct an event from a plain object | every consumer needs it; it is how an event arrives from a queue or a file |
| `validate` | check an event against its published schema, reporting the failing field path | checking conformance is the one thing a *standard's* SDK exists to make easy |
| `compute_content_hash` | the digest the specification defines | it is a **specified algorithm**; two SDKs that compute it differently break deduplication across implementations, silently |
| `schema_uri_for` | the canonical schema URI for an event type | it is how `dataschema` gets set correctly rather than guessed |
| `vocabulary` | the **10 published enumerations** | without it users hardcode strings, and a catalog that grows never reaches them |

**What each `required: true` costs, measured against
`surface.json` (2026-09-06, and `tests/test_surface.py` fails if a declaration
stops matching the code):**

| | Python | TypeScript |
|---|---|---|
| `build` 7/7 | ✅ | ✅ |
| `from_object` | ✅ as `from_dict` | ✅ as `fromJSON` |
| **`validate`** | ✅ | **🔴 absent** |
| `compute_content_hash` | ✅ | ✅ |
| `schema_uri_for` | ✅ | ✅ |
| `vocabulary` 10/10 | ✅ | ✅ |

So the cost is **one capability in one library**, plus a rename with aliases in
both (§4). `@iaes/sdk` cannot validate an event against its schema today, and it
is the SDK both flow runtimes depend on.

That gap is not a reason to drop `validate` from the profile. Writing the
requirement around what the steward already ships would be a vendor-specific
requirement wearing a general shape, and §8 item 4 says those do not appear.
Either the gap closes before the release that adopts the profile, or the release
publishes the profile alongside the steward's own non-compliance with it.

**`iaes-opta-runtime` claims nothing.** It is a microcontroller runtime with two
of seven builders and one of ten vocabularies. It is wire-conformant, it is a
reference implementation, and under §9.2 not claiming a profile is not a
deficiency. Widening the profile until it fit would empty the profile of
meaning.

## 3.2. What is not required, and why

**`route`** — dispatch by event type. `surface.json` already recorded the
reason, and it is the right one: *a library caller uses a switch*. Requiring
every library to ship a dispatcher would be requiring an opinion about program
structure, which is not what a wire standard's SDK owes anyone. It stays a
capability that flow runtimes have because dispatch is what a flow runtime *is*.

**Publishing.** `surface.json` lists it under `not_capabilities` and the reason
survives inspection: IAES defines no transport, no endpoint contract and no
delivery negotiation, so there is nothing for a second implementation to conform
to. A function that sends is a client for a particular server. It becomes a
capability the day a transport binding exists — and if one ever does, that is a
change to an adopted profile, classified under §4.4, not a detail.

# 4. Names

> **[TEXT]** The same word, in each language's convention. Never a different
> verb.
>
> The canonical name for constructing an event from a plain object is
> **`from_object`**. Existing names — `from_dict` in Python, `fromJSON` in
> TypeScript — become **deprecated aliases**. They keep working.

`compute_content_hash` and `computeContentHash` are one capability spelled by
two languages, and that is correct. `from_dict` and `fromJSON` are two verbs,
and a reader cannot tell whether they do the same thing without opening both.

The aliases are kept rather than removed for a reason that outlives this memo:
removing them would break every caller, which would make a naming decision into
a MAJOR change and teach that tidying the surface is expensive. Deprecation
costs nothing and says the same thing.

# 5. Failure

> **[TEXT]** A validation failure MUST report **that it failed** and **the path
> of the offending field**.
>
> The type raised, its name, and the mechanism — exception, result type, error
> value — are the language's business and are not part of the profile.

`surface.json` is blunt about the state of this, and the assessment is worth
keeping rather than smoothing over:

> Python raises `ValidationError` and TypeScript has `IaesClientError`, and they
> do not do the same thing. This is the least-examined part of the surface and
> the most consequential for someone moving between languages.

This memo requires the two facts and stops there. Requiring a shared error
*shape* across a language with exceptions, one with result types and one with
neither would be designing a cross-language error model inside a profile
adoption — and it would be designed from two data points. The gap is named so
that the next memo about it starts from a stated limit rather than from silence.

# 6. How a library claims the profile

> **[TEXT]** A library claims the profile by stating, in its published
> documentation, that it implements **the IAES SDK profile of IAES 2.0**.
>
> The claim is checked against `surface.json` in that release. No registration,
> no notification, and no involvement by the steward (§9.3).

Deliberately not a metadata key. npm, PyPI, Maven and NuGet each spell package
metadata differently, and a profile that required a particular field would be
requiring an ecosystem — which the standard has no business doing, and which
would make the claim unavailable to whoever ships somewhere we did not think of.

A sentence in the documentation is checkable by a human in a minute and by a
script in an afternoon, in every ecosystem that exists.

# 7. No levels in 2.0

Levels were considered and are not adopted. With the scope in §2 there is **one
artifact class**, and a level structure over one class is ceremony: it would
multiply what a claim can mean without making any claim more precise.

The pressure that suggested levels came from trying to fit the node packages and
the microcontroller runtime into one profile. §2 removes that pressure by
scoping the profile rather than by grading it.

If a second artifact class ever adopts a profile, it gets its own — not a level
of this one. Two profiles for two kinds of artifact is clearer than one profile
with tiers that exist to excuse the mismatch.

# 8. Compatibility level of this change

**MINOR, derived under §4.5.**

```
R1  reduction?      No. Nothing an implementer was entitled to rely on becomes
                    something they are not. Wire conformance is untouched, and
                    no library was conforming to a profile that did not exist.
R2  classification  No. This memo states no rule about how future changes are
    only?           classified.
R3  addition?       Yes. It adds a profile nobody is obliged to claim, and the
                    steward's obligation to carry its definition in the release
                    (§9.4). Reduces nothing.  ->  MINOR
```

⚠️ **This is the last time adopting a profile is this cheap.** Once
`surface.json` is normative, adding a required capability makes libraries that
claim the profile non-conforming to it — an obligation change, which is §4.4's
domain, and which will have to be confirmed there rather than assumed.

# 9. Effect on existing implementers

**No implementation has anything to do, and no reliance is reduced.** The
profile binds nobody who does not claim it, and a wire-conformant system stays
wire-conformant.

For the steward's own packages the effect is concrete and stated rather than
implied: `@iaes/sdk` must gain `validate`, and both SDKs gain `from_object` as
the canonical name with their present names kept as deprecated aliases, before
`@iaes/sdk` or `iaes` can claim the profile they publish.

# 10. What this memo does not decide

- **A flow-runtime profile.** Out of scope by §2, and a separate adoption if
  ever wanted.
- **A cross-language error model.** §5 requires two facts and names the rest as
  the least-examined part of the surface.
- **Anything about transport.** Publishing stays outside the standard until a
  transport binding exists.
- **Anything about the wire.** No field, no schema, no obligation on any
  producer or consumer.

# 11. Proposed incorporation

1. **`surface.json` becomes normative**, `state: "normative"`, naming IAES 2.0
   as the release whose profile it defines, with §2 through §5 of this memo
   recorded in it: the library scope, the six required capabilities, `route` not
   required, the canonical name and its aliases, and the failure requirement.
2. **`surface.json` enters the release manifest's normative set**, per
   `GOVERNANCE.md` §9.4 — a claim names a release and is checked against that
   release's definition.

   **`SDK_SURFACE.md` does not.** An earlier draft put both there, which would
   have made the reasoning normative alongside the definition it explains: two
   authorities over the same thing, which is the shape `IAES-RFC-000` and
   `GOVERNANCE.md` §6.1 already closed for RFCs. It keeps travelling in the
   repository and explaining the profile; it does not govern it, and it says so
   in its own header.
3. **`GOVERNANCE.md` §9.2** stops saying that no profile is adopted, and names
   the profile IAES 2.0 adopts and where its definition lives.

`GOVERNANCE.md` §9.1, §9.3, §9.4 and §9.5 are unchanged, and so is every section
before §9.

# Author

G. Garza, Wertek AI, Inc. — steward of the Industrial Asset Event Standard.
