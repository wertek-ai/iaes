# The IAES Philosophy

> **Not normative.** This document explains why IAES is shaped the way it is.
> What IAES *requires* is in `IAES_SPEC.md`; how it *changes* is in
> `GOVERNANCE.md`. Where this document and those disagree, they govern —
> `GOVERNANCE.md` §2.
>
> It cites rather than restates. A summary of a rule drifts from the rule and
> then quietly replaces it: `GOVERNANCE.md` §6.1 once illustrated a point with
> an example that had since become false about its own repository, and nobody
> noticed for a release. Every claim below points at the text that carries it,
> so a reader can check it and a maintainer can see what breaks when the rule
> moves.

## The gap

A vibration model concludes that a bearing is failing. A CMMS needs to open a
work order. Between those two facts sits an integration: someone's JSON, in
someone's shape, over someone's transport, written once for that pair and
rewritten for the next one.

The industry is not short of standards. OPC UA moves values. Sparkplug B moves
them efficiently over MQTT. ISO 14224 says how to record reliability data.
Asset Administration Shell describes a digital twin. What none of them settles
is the small, boring thing in the middle: **what a finished industrial judgment
looks like on the wire, so that anything can emit it and anything can read it.**

IAES is that envelope and nothing more. `IAES_SPEC.md`, Purpose, states the
scope; `GOVERNANCE.md` §1 states the boundary — no asset hierarchy, no
equipment catalog, no commercial terms.

## Seven stances, and what each one costs

### 1. The standard depends on nothing of ours

A reader must be able to implement IAES without asking us anything and without
pointing at anything of ours. `GOVERNANCE.md` §1 states it; `GOVERNANCE.md` §1.1 makes it
mechanical, and every repository carrying the IAES name runs the check.

**Why it needs a check.** A violation does not look like our name in the text.
It looks like a default value, an example payload, or a topic layout that
happens to encode our operating model. Attribution is fine — *IAES is
maintained by Wertek AI* is a fact. Shipping our ingest host as a default is
not: a reader who installs the node and clicks through is pointed at our server
without being told.

**What it costs.** We cannot make the standard convenient for ourselves. Any
convenience we would want has to be available to everyone, or it does not ship.

### 2. Citation is not conformance

IAES names industrial standards where they supply context or a vocabulary
defined outside it. Naming one does not certify an implementation against it.

`IAES_SPEC.md`, References, asks two separate questions of every reference —
whether the value must satisfy that document for the event to conform, and
whether the schema rejects a value that does not — and publishes where they
disagree. Today exactly one reference is normative for meaning, and even there
the schema checks the shape and not the list.

**What it costs.** Earlier IAES material called itself *ISO-aligned* and
described a field-level mapping to four documents. IAES 2.0 withdrew those
claims, because the correspondence had never been verified against the cited
document and three of the four had never been read. The withdrawal removed a
sentence that made the standard sound more established than it was. That is the
price, and it is worth paying: a claim nobody checked is a claim that fails at
the worst moment, in front of the reader who does check it.

### 3. Conformance is claimed and checked, never granted

Wire conformance is what conforming to IAES means unqualified: the event
validates and satisfies what the specification requires of it. There is also a
library profile, and `GOVERNANCE.md` §9.3 fixes who decides: a library *claims*
it, anyone *checks* it against `surface.json` in the release it names, and
**nobody grants it.**

**Why.** `GOVERNANCE.md` §1 forbids a rule that needs a specific vendor's judgment to be
meaningful, and the steward is a vendor. A certification programme would
reintroduce exactly that dependency through another door.

**What it costs.** We give up the one thing a steward is usually tempted by —
being the party who says yes. Not claiming a profile is not a deficiency
(`GOVERNANCE.md` §9.3), and an implementation that never speaks to us is as conforming as one
that does.

### 4. Silence is not an assertion

A producer that was not given a value MUST omit the field rather than
substitute one, and a consumer MUST NOT read absence as a default. This is
stated in `IAES_SPEC.md` and decided in `rfc/IAES-RFC-002.md`.

The same idea runs through the compatibility policy in the other direction:
behaviour a version did not specify is not guaranteed across versions
(`GOVERNANCE.md` §8), and silence in a prior version is neither permission nor
promise (`GOVERNANCE.md` §4.4).

**What it costs.** Substituting a plausible default is friendlier in the short
run and produces a dataset that quietly lies. A `0.0` that means *nobody
measured this* is indistinguishable, six months later, from a `0.0` that means
*this reading was zero*.

### 5. The catalog is open

`event_type` is a pattern, not a list. A producer MAY define its own type in a
namespace it controls, and a consumer MUST NOT error on one it does not
recognise. The seven published types are interoperability defaults, not the
limit. `measurement_type` works the same way: any published list is advisory.

**Why it had to be fixed.** The field was a closed enumeration while the same
document ordered consumers to tolerate values they did not recognise — a
contradiction that made an unknown type impossible to produce. Both flow
validators then reintroduced the closed list in their own code, which is how a
contradiction survives being corrected once.

**What it costs.** We cannot promise that every IAES event is one of seven
known shapes. What we promise instead is that an unknown one does not break the
reader.

### 6. A release is one indivisible object

A specification release is the specification, the governance document, the
schemas and the accepted RFCs, published together under one tag; it is what a
DOI refers to. A package is the other kind of release and carries neither a
specification nor a DOI of its own. `GOVERNANCE.md` §3-bis.

A published version stays retrievable at its own URI and DOI, and a
representation served under a major's URI stays that major's — it is never
regenerated from a later release.

**What it costs.** Fixing a typo in a published release is not possible. It
becomes an erratum in the next one, and the wrong text stays visible with an
explanation. We have exercised this: `rfc/IAES-RFC-009.md` corrects a
misattribution in Appendix C and explicitly leaves 2.0 as published.

### 7. Publish what the artifacts do not check

`IAES_SPEC.md`, References, records that `format` is an annotation in JSON
Schema Draft 2020-12, so the schemas assert nothing about RFC 3339, RFC 4122 or
RFC 3986; and that `^[A-Z]{3}$` checks the shape of a currency code and not its
membership, so `ZZZ` validates.

**Why.** An event can be schema-valid and non-conforming. A reader who assumes
the schema is the whole contract will ship something that validates and is
wrong. The limits of the machine-checkable part are the steward's to publish,
and they are exactly what a steward is tempted to leave unsaid.

## What holds this together

None of the above survives on care. Each stance that could be checked
mechanically is checked, in CI, and each check was written because the thing it
watches had already gone wrong at least once — not because it seemed prudent.
`AGENTS.md` records the method.

That is the whole design in one line: **a standard is only as good as the
number of its promises that something other than good intentions is keeping.**

---

*Maintained by Wertek AI, Inc. Licensed CC BY 4.0. Implementations are listed
in `README.md`; none of them is privileged.*
