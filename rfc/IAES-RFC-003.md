```
IAES                                                        G. Garza
Request for Comments: 003                                   Wertek AI
Category: Process                                    September 2026
ISSN: N/A

    Classifying Changes to Producer and Consumer Obligations
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

This memo proposes an addition to the compatibility policy in `GOVERNANCE.md`
§4. It defines no wire format and changes no schema.

**State: Accepted**, per `GOVERNANCE.md` §6. **Compatibility: MAJOR. Target
version: IAES 2.0.** Distribution is unlimited.

It reached Accepted the long way. §4 has no rule that classifies a change to
the compatibility policy itself, so this memo could not state its own
compatibility level — which §6 requires of every RFC — and it said so instead
of choosing a convenient one. The steward decided under the authority that
exists (§5), not under a rule written for the occasion.

§2 keeps the framings this criterion rejected — including the one this memo
drafted first — because a criterion is easier to trust when the shapes it
turned down are visible.

# Copyright Notice

Copyright (c) 2026 Wertek AI, Inc. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

`GOVERNANCE.md` §3 says MAJOR is *anything that can break an existing producer
or consumer*. §4.2 operationalises that in five criteria: four are shaped like
schema changes, and the fifth — *changing the meaning or the unit of an
existing field while keeping its name* — already reaches past the schema into
what a value means.

Between them they classify a great many obligations: making an optional field
required changes what a producer must do, and so does narrowing a constraint.
What the five do **not** reach is the residual — an obligation on a producer or
a consumer that is classified neither as a change to the representation nor as
a change to an existing field's meaning. That residual has a category and no
test.

This memo supplies the test. It asks whether the change breaks the
**interoperability guarantee** §4 exists to protect — that a consumer built for
version *N+1* can still read events produced against *N*, with the meaning *N*
gave them — and it draws one distinction that decides most cases: whether the
new obligation *supplies* a meaning the standard had left unstated, or
*changes* one the standard had already given.

# 1. What raised it

A drafted change would oblige a producer to omit an optional field it was not
given, rather than substitute a value. Measured against §4.2, it is none of the
five: it makes no optional field required, removes and renames nothing, narrows
no constraint, changes no existing field's meaning or unit, moves no `$id`.
Every schema is byte-identical before and after.

Reading it MINOR because nothing stops validating uses a test §4.2 does not
offer. Reading it MAJOR by analogy invents one. The gap is worth closing before
it is worked around, because every future decision of this shape hits it.

# 2. Two framings that do not work

**The first proves too much.** *A new obligation makes a previously conforming
producer non-conforming, therefore MAJOR.* Every new obligation does that, at
the new version. Under that rule MINOR could never carry a MUST, and the only
compatible change would be one nobody has to implement — a freeze, not a
policy.

The error is the frame. Conformance is not a property an implementation has in
the abstract; it is a property it has **against a version it declares**. An
implementation that declares 1.4 is measured against 1.4 for as long as 1.4 is
published, and `GOVERNANCE.md` §4.3 keeps that at least 24 months.

**The second proves too little,** and it is the one this memo drafted first:
*does an implementation that declares N stop conforming to N?* Under IAES's own
rules a published version is immutable, so a later version **cannot** make an
implementation stop conforming to the version it declares. The test is
answerable in advance, always the same way, and every obligation not already
caught upstream falls out of it as MINOR.

A test that cannot return both answers is not a test. It is a formality that
launders whatever the previous steps left over.

What §4 is actually protecting is not the past version's self-consistency — that
is guaranteed by publication — but the **guarantee between versions**: a
consumer built for *N+1* can read events produced against *N*. That is the
property a change to an obligation can genuinely break, so that is what the
third test must ask.

# 3. The criterion

> **[TEXT]** Apply `GOVERNANCE.md` §4.1 and §4.2 first. If the change is
> classified there, that classification governs and this section does not
> apply.
>
> A change to an obligation on a producer or a consumer that §4.1 and §4.2 do
> **not** otherwise classify is classified by the two tests below, in order.
> The first that answers, decides.
>
> **T1 — MEANING.** Must the same bytes, valid under version *N*, now be
> interpreted with a different meaning?
> If yes: **MAJOR**.
>
> §4.2 already says this of a **named field**. T1 is the same rule for meaning
> a version stated by other means — what the *absence* of a field asserts, what
> a combination of fields asserts — which is why it is reached only for changes
> §4.2 does not already classify.
>
> Meaning is *changed* only where the previous version **stated** one. Where
> the previous version was silent, the new version **supplies** a meaning, and
> supplying is not changing: there was no rule to contradict.
>
> Silence is not permission. A producer whose behaviour the previous version
> never addressed was not authorised by it; it was simply unaddressed, and the
> new obligation is the first rule on the point rather than a reversal of one.
> Nor is silence a guarantee: where the standard said nothing, implementations
> may have assumed different things, and a consumer whose assumption the new
> obligation contradicts may well break. **That is a broken expectation, not a
> broken guarantee** — the compatibility promise covers what a version stated,
> and cannot cover what it left open. Where such an expectation is known to be
> widespread, the change is still MINOR under this section and the release
> notes carry the warning.
>
> **T2 — CROSS-VERSION INTEROPERABILITY.** Under the compatibility direction
> §4 promises, can a consumer that declares *N+1* still consume an event that
> conforms to *N*, with the meaning *N* gave it?
> If no: **MAJOR**.
> If yes, the obligation may be **MINOR**, provided only implementations that
> declare *N+1* have to adopt the new behaviour.
>
> An obligation that only restates what the existing normative text already
> required is **PATCH**, per §3.

Three notes on why it is shaped this way.

**§4.1 and §4.2 come first, and are not restated here.** An earlier draft
opened with *does data that was valid become invalid?* — which §4.2 already
answers, and which cannot arise for a change that reaches this section at all.
Asking it made the section look complete and made its own scope incoherent.

The same draft described §4.1 and §4.2 as classifying *the representation*, and
that is measurably not what they do: the fourth criterion in §4.2 is a rule
about **meaning**, and a version can change a field's stated meaning without
touching a byte of any schema. The boundary is therefore not *schema change
versus no schema change*. It is **already classified there versus residual**,
and this section only ever handles the residual.

**T1 before T2.** A change of meaning can leave every event consumable —
parsed, accepted, no error anywhere — and still be read wrongly. That is the
worst failure this policy exists to prevent, and it is silent, so it is asked
first.

**T2 is asked in the promised direction, not both.** §4 guarantees BACKWARD:
consumers update first, producers follow. A consumer at *N* meeting an event
from *N+1* is outside the guarantee, and demanding it would classify every
addition as breaking.

A fourth note, on the reasoning most easily abused. *The previous version did
not forbid it* is not by itself an argument for MINOR, and this section must
not be read as making it one. It answers T1 — there was no stated meaning to
change — and answers nothing else. T2 is still asked, and asked about events,
not about intentions: an obligation that leaves a 1.4 event unreadable or
re-readable by a 1.5 consumer is MAJOR however silent 1.4 was.

# 4. Applying it to the case in §1

**§4.1 and §4.2 first.** None of the five applies: no schema changes, and no
existing field's stated meaning changes — `anomaly_score: 0.0` meant *the score
is zero* before and means it after. Not classified there, so the tests apply.

**T1 — meaning.** The previous version stated no meaning for an absent optional
field. A consumer that defaulted an absent `anomaly_score` to `0.0` was filling
a gap, not following a rule. The obligation **supplies** the meaning. **No.**

**T2 — cross-version interoperability.** Two directions to walk, and both hold:

```
producer 1.4:  anomaly_score = 0.0          (1.4 stated no rule either way)
      ↓
consumer 1.5:  reads 0.0 as 0.0             same meaning, nothing to re-read

producer 1.5:  no measurement -> omits the field
      ↓
consumer 1.5:  the field was already optional; absent is valid
```

A consumer that declares 1.5 consumes 1.4 events with the meaning 1.4 gave
them. **Yes.**

The distinction that carries this is worth stating exactly. 1.4 *did* state
what `anomaly_score: 0.0` means: the score is zero. What it never stated was
whether a producer may write that when it has no score. The obligation changes
the second and leaves the first alone — a rule about **what a producer may
assert**, not about **what a value means** — which is why every byte already on
the wire keeps its reading.

And the proviso holds: the new MUST binds only an implementation that wants to
declare 1.5. A producer that keeps declaring 1.4 keeps substituting and remains
conforming to 1.4, because 1.4 required nothing of it here, for as long as 1.4
is published.

**MINOR** — derived, not assumed. The point of the derivation is that it could
have come out the other way: had 1.4 stated that an absent `anomaly_score`
means zero, T1 would have caught it, and no amount of "the bytes did not
change" would have rescued it.

# 5. Compatibility level of this change

**MAJOR. Target version: IAES 2.0.**

Not derived from a rule for changes of this kind, because §4 has none. Decided
by the steward under the authority that exists, and §5.1 records what that
authority says. An earlier draft of this section claimed MINOR on the ground
that no event, schema, field meaning or producer obligation changes — true, and
not a criterion: no such rule exists in §4. The new §4.4 does not supply one
either, being scoped to obligations on producers and consumers, which this
change is not. What this change alters is:

```
the compatibility policy itself
the definition of MAJOR
what implementers may rely on
an obligation of the steward (disclosure)
```

## 5.1. Measured: no authority reaches it

Every nearby clause was read, and each excludes itself:

| clause | what it covers | why it does not reach this change |
|---|---|---|
| §3, PATCH | *Editorial only. No change to any schema.* | amending a normative guarantee is not editorial |
| §4.1, last bullet | *adding, correcting, or clarifying **non-normative** text* | GOVERNANCE.md is normative in its header; §8 is not an example or a note |
| §4.2 | five criteria | every one is about an event, a field, a catalog or a schema |
| §4.4 | producer and consumer obligations | scoped away from the policy itself, on purpose |
| §5.1 | a `$id` that never resolved | narrow by construction, and forbids carrying any other change |
| §1, item 1 | one boundary commitment | *«not subject to change by a minor release»* |

Two of those rows decide more than the others.

**§5.1 is the only exception the standard grants, and its stated ground is
dependability**: *an `$id` that has never been resolvable was never a usable
identity, and **no implementer can have depended on it***. Applied here the
principle points the other way — §8 is titled *What implementers can rely on*,
it is normative, and an implementer could depend on item 2 precisely because it
invited them to. Whether §4 could back the promise is the steward's problem, not
theirs.

**§1 item 1 is the only place GOVERNANCE classifies a change to one of its own
commitments**, and what it says is that the commitment is *not subject to change
by a minor release*. It is scoped to one boundary and is not a general rule, but
it is the only on-point precedent, and it does not point at MINOR.

**Conclusion: nothing licenses MINOR, and the nearest authority points away from
it.**

## 5.2. The decision, and the order it is taken in

**MAJOR, under existing authority, and §4.5 afterwards.** Three options were on
the table; the reasoning that chose between them is worth keeping, because the
one that was rejected is the more tempting.

**Rejected: write §4.5 first and let it classify this change.** A rule that is
not yet authority must not grant itself the authority to enter as MINOR. That is
the bootstrap this repository already met once — `IAES-RFC-000` records it: *a
change process cannot govern the change that creates it* — and having learned to
name it, using it as a shortcut would be worse than not having learned.

**Taken: the existing authority is enough for the conservative answer.** §8 item
2 promised that a MINOR release will not break a working integration, and this
memo openly reduces that reliance for unspecified behaviour. §5.1, the only
comparable exception, licenses MINOR precisely because *no implementer can have
depended on* the defective identity — and here the opposite holds: §8 invited
the dependency. §1 item 1, the only clause that classifies a change to one of
GOVERNANCE's own commitments, says such a commitment is *not subject to change
by a minor release*.

Neither clause was written for this case. Both point the same way, and nothing
points the other.

### What §4.5 is for, and what it is not for

The second-order gap is real and stays open until it is closed prospectively:

```
§4.1 / §4.2   representation, and a named field's meaning
§4.4          residual producer and consumer obligations
§4.5          changes to the compatibility policy itself        ← still to write
              changes to what implementers may rely on
              changes to the steward's own obligations
```

§4.5 will be written in its own memo and **may travel inside 2.0 alongside this
one**. It is not used to legitimise this memo's entry retroactively. Its purpose
is that this gap never has to be decided by judgment again.

It does not belong inside §4.4: folding *changes to the policy* into a
subsection about *producer and consumer obligations* would mix two domains,
which is the defect §4.4 exists to have avoided.

### What 2.0 means here

`GOVERNANCE.md` has no version of its own. §3-bis makes a specification release
indivisible — the specification, this document, the schemas and the accepted
RFCs under one tag, with one DOI — so a MAJOR change to governance carries the
whole standard.

That is the right result rather than an accident of packaging:

> **IAES 2.0 is the first version whose technical contract and whose contract
> of evolution are both closed.**

Materially changing what an implementer is authorised to rely on is a break in
the standard even when no payload changes. A version number that moved only for
payloads would be describing half the standard.

### Measured: 2.0 is not free of schema work

*«2.0 without touching a schema»* is not available, and the reason is in the
schemas rather than in this memo:

| where | today | consequence |
|---|---|---|
| `iaes-envelope.schema.json`, `spec_version` | `^1\.[0-9]+$` | an event declaring `2.0` **fails validation** against every published schema |
| all eight `$id`s | `https://iaes.dev/schema/v1/…` | a major line needs its own identity; §4.2 already calls a `$id` change MAJOR |

Both are release work and neither belongs in this memo. They are named here so
the release is planned rather than discovered: the 2.0 cut has to widen or
re-major the `spec_version` pattern, publish the schemas under a `v2` identity,
keep every `v1` identity resolvable forever (§8 item 1), and carry the version
history entry and migration statement §8 item 3 requires.

# 6. Effect on existing implementers

**No implementation has to change. Some reliance does.** Those are different
claims, and an earlier draft of this section collapsed them into *«None»*.

Nothing at runtime moves. An implementation conforming to 1.4 remains
conforming, no producer changes what it emits, no consumer changes what it
accepts, and no deployed integration behaves differently because this memo was
accepted.

But an implementer was entitled by §8 item 2 to rely on *a MINOR release will
not break a working integration*, and after §8.4 that entitlement is narrower:
it covers behaviour a version specified, and no longer covers behaviour it left
open. Nobody has code to write; an implementer whose upgrade policy said *MINOR
releases can be taken without review* has a policy to revisit, and is owed the
disclosure §8.4 now requires in exchange.

That distinction — **no work, less reliance** — is why §5 cannot call this
change MINOR by observing that no runtime is affected.

# 7. What this memo does not decide

- **Whether a second class of conformance exists** beside wire conformance —
  an SDK surface, a package's documented API — and who would grant it. The
  tests above are written for obligations on producers and consumers of
  events. Extending them elsewhere requires deciding that question first.
- **Anything about `format`.** Whether the specification's prose promises more
  than the schemas assert is a separate finding, and its remedy is a change to
  the **representation** — a narrowing under §4.2, which §4.1 and §4.2 already
  classify without help from this section.
- **Retroactive reclassification.** Releases already published keep the
  classification they were published with.

# 8. Proposed incorporation

The criterion cannot be added as one new subsection. Two sentences already in
`GOVERNANCE.md` promise something broader than §4 guarantees, and leaving them
standing beside §4.4 would put the document in contradiction with itself —
which is the failure this project has spent a fortnight learning to look for.
**A local rule is not incorporated until the surrounding authority agrees with
it.**

Four amendments, and they are one change.

## 8.1. §3 — what MAJOR means

The table today reads:

> **MAJOR** — Anything that can break an existing producer or consumer.

Read literally beside §4.4, that is a contradiction: this memo says a consumer
that relied on unspecified behaviour may break and the change is still MINOR.
Both cannot stand. Replace with:

> **MAJOR** — Anything that breaks the compatibility guarantee defined in §4.

**It is a narrower promise, and saying otherwise would be false.** The
accounting is:

```
before:  a working integration                      → protected

after:   an integration relying on specified
         behaviour                                  → protected
         an integration relying on unspecified
         behaviour                                  → not protected
                                                    → disclosed, where the risk
                                                      is known
```

Less guarantee of non-breakage, more guarantee of transparency. That is a trade,
not an equivalence, and the disclosure obligation does not return the guarantee
it replaces.

What justifies the trade is that the wider promise was one the standard could
not keep: a version can guarantee what it **said**, and cannot guarantee what it
left open, because it does not know what anyone inferred from the silence. But
being unkeepable is a reason to change a promise — it is not, by itself,
authority to change it at any particular release level. That question is §5.

## 8.2. §4.2 — the pointer, and what it must not say

At the end of §4.2:

> A change to a producer or consumer obligation that is not otherwise
> classified by §4.1 or §4.2 is classified under §4.4.

The wording matters. An earlier draft of this memo said *a change that alters
an obligation without altering a schema*, and that is false: §4.2's fourth
criterion — *changing the meaning or the unit of an existing field while
keeping its name* — needs no schema change at all. A version can redefine
`severity` from *condition of the asset* to *urgency of the response* in prose
alone, and §4.2 already classifies that MAJOR.

So the boundary is **already classified there versus residual**, never *schema
versus no schema*. §4.1 and §4.2 are unchanged in substance and are applied
first.

## 8.3. §4.4 — the criterion

§3 of this memo, as a new subsection after §4.3, titled *Changes to producer
and consumer obligations*.

## 8.4. §8 — what implementers can rely on

Item 2 today reads:

> A MINOR release will not break a working integration.

A working integration includes one that depends on behaviour no version ever
specified, so as written the sentence promises what §4 cannot deliver. Replace
with:

> A MINOR release preserves the BACKWARD compatibility guarantee in §4.
> Behaviour a prior version did not specify is not guaranteed across versions.
> Known risks involving such behaviour are disclosed in the release notes.

The third sentence is the part that keeps this honest. Narrowing a promise
without owing anything in return would be a downgrade; the disclosure
obligation is what the steward gives back, and it is normative.

## 8.5. Why all four in one release

§4.4 alone would leave `GOVERNANCE.md` asserting two incompatible definitions
of *break*, in §3 and in §4.4, two sections apart. That is the exact shape of
the defect this repository has already paid for once: a canonical document that
contradicted itself two sections apart, and two readers with the document open
deduced opposite repairs.

They ship together, in **IAES 2.0**, or not at all.

# Author

G. Garza, Wertek AI, Inc. — steward of the Industrial Asset Event Standard.
