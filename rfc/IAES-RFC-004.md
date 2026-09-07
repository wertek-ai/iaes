```
IAES                                                        G. Garza
Request for Comments: 004                                   Wertek AI
Category: Process                                    September 2026
ISSN: N/A

      Classifying Changes to the Compatibility Policy Itself
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

This memo proposes a new subsection of `GOVERNANCE.md` §4. It defines no wire
format and changes no schema.

**State: Accepted**, per `GOVERNANCE.md` §6.
**Compatibility: MINOR — a steward's decision under existing authority, not a
derivation, and expressly not derived from the rule this memo proposes (§5).
Target version: IAES 2.0.** Distribution is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI, Inc. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

`IAES-RFC-003` closed the gap between §4.2 and changes to producer and consumer
obligations. Incorporating it opened the next one: to fit §4.4 into
`GOVERNANCE.md`, two promises the document had already made had to be reduced,
and **§4 has no rule for classifying a change to itself**.

That gap was decided once, by judgment, under the authority that existed. This
memo makes sure it is not decided by judgment twice. It proposes §4.5 for
changes to the compatibility policy, to what implementers may rely on, and to
the steward's own obligations — and a second rule that has been used three times
without ever being written down: **the level of a release is the maximum level
of the changes it incorporates.**

# Table of Contents

    1. What raised it
    2. The domain, and why it is not §4.4
    3. The rule
       3.1. Why the classification test comes second, and carries a guard
    4. The level of a release
    5. Compatibility level of this change
    6. Effect on existing implementers
    7. What this memo does not decide
    8. Proposed incorporation

# 1. What raised it

`IAES-RFC-003` §5 recorded the problem in full. In short: incorporating a
criterion for producer and consumer obligations required amending §3's
definition of MAJOR and item 2 of §8, because both promised something broader
than §4 could deliver. Both amendments **reduced** what an implementer had been
told they could rely on.

Measured against §4 as it then stood, no clause reached the case. §3's PATCH is
editorial only; §4.1's text bullet is scoped to *non-normative* text; §4.2's
five criteria are about events, fields, catalogs and schemas; §4.4 is about
obligations on producers and consumers. Two clauses came close and neither was
written for it: §5.1, whose stated ground is that *no implementer can have
depended on* the defect being corrected, and §1 item 1, which says one boundary
commitment is *not subject to change by a minor release*.

The steward decided MAJOR on that reading. The decision was sound and the
process it used does not scale: the next change of this shape would arrive with
the same absence and a different reader.

# 2. The domain, and why it is not §4.4

§4.4 classifies changes to obligations on **producers and consumers**. The
changes this memo is about are of a different kind: they alter the policy that
does the classifying, the guarantees §8 states, or what the **steward** owes.

Folding one into the other would mix two domains, and the mixing is not
cosmetic. §4.4's tests ask what happens to an event and to the implementations
that exchange it. The questions here have no event in them at all.

They are also asymmetric in a way §4.4 is not: a producer's obligation binds
whoever adopts a version, while a guarantee in §8 binds **the steward toward
everyone who adopted any version**, including versions published years earlier.
A rule that cannot see that difference will eventually let a promise be reduced
because the change looked small from inside the current release.

# 3. The rule

> **[TEXT]** This subsection classifies a change to this policy, to §8, or to
> an obligation of the steward. Apply the tests in order; the first that
> answers, decides.
>
> **R1 — REDUCTION.** Does the change remove a guarantee a published version
> gave to implementers, or narrow the conditions under which that guarantee
> holds? If yes: **MAJOR**.
>
> A guarantee is *reduced* when something an implementer was entitled to rely
> on becomes something they are not, whether by withdrawing it, by adding a
> condition to it, or by redefining a term it depends on.
>
> **R2 — CLASSIFICATION ONLY.** Does the change state or refine how future
> changes are classified, altering no guarantee in either direction? If yes:
> **MINOR**.
>
> **R2 does not apply to a change that states a classification rule and, in
> doing so, reduces a guarantee.** Such a change is R1. The form a change takes
> does not determine its level; what it does to a published guarantee does.
>
> **R3 — ADDITION.** Does the change add a guarantee, or add or widen an
> obligation of the steward, reducing nothing? If yes: **MINOR**.
>
> An amendment that only corrects a typographical or formatting defect, leaving
> every guarantee and obligation identical, is **PATCH** per §3.

## 3.1. Why the classification test comes second, and carries a guard

**The order was wrong in the first draft of this memo, and the error was the
one this memo exists to prevent.** The tests were R1 reduction, R2 addition,
R3 classification-only — and a classification rule *obliges the steward to
classify future changes a particular way*, which is an obligation of the
steward, which answers R2. Every case R3 was written for would have been
absorbed one test earlier, and **R3 would have been unreachable**: present in
the document, never applying to anything.

That is the same defect as the third test `IAES-RFC-003` had to replace, in the
other direction. There a test could never return MAJOR; here a test could never
be reached at all. Both look like a complete framework and neither
discriminates.

**A test that an earlier test absorbs is not a test.** Classification-only now
runs second, before addition, so each of the three is reachable. No level
changes: a classification rule was always meant to be MINOR, and it still is.

Without its guard, the classification test is the hole through which every
reduction escapes.

`IAES-RFC-003` is the worked example, and it is not hypothetical. Presented one
way it is a pure classification change: it adds §4.4, a rule for classifying
future changes, and touches no event. Presented honestly it also **narrows the
definition of MAJOR and withdraws part of §8 item 2** — and those are R1. A rule
that let the first description govern would have produced MINOR for a change the
steward correctly called MAJOR.

That is why R1 runs first and why R2 names the case explicitly rather than
leaving it to good faith. **A test that can be satisfied by how a change is
described, rather than by what it does, is not a test.**

# 4. The level of a release

> **[TEXT]** The level of a release is the **maximum** level of the changes it
> incorporates, ordered `PATCH < MINOR < MAJOR`.
>
> A release does not take a lower level because most of the changes it carries
> are minor, and does not take a higher one because it is large. One MAJOR
> change makes the release MAJOR whatever else travels with it.
>
> This applies to releases made after it takes effect.

This has been true of every release IAES has made and was never written down.
`IAES-RFC-002` is the case that makes it visible: measured decision by
decision, it is **MINOR**, and it ships inside **2.0** because
`IAES-RFC-003` travels in the same release. Without this rule that pairing has
no stated justification, and a reader could reasonably conclude that either the
memo or the release had been misclassified.

The prospective clause matters for the same reason the rest of this memo does:
IAES 1.0 through 1.4 were classified without it, and reclassifying a published
release would contradict §8 item 1, which says published versions are never
edited in place.

# 5. Compatibility level of this change

**MINOR** — and stated as a steward's decision rather than a derivation, on
purpose.

**This memo does not classify itself under §4.5.** A rule that is not yet
authority must not grant itself the authority under which it enters. That is the
bootstrap `IAES-RFC-000` recorded — *a change process cannot govern the change
that creates it* — and it is the reason `IAES-RFC-003` was not allowed to wait
for this memo to be written first.

Under the authority that exists, measured the same way §5.1 of that memo
measured it:

- **Nothing is reduced.** No guarantee in §8 is withdrawn or conditioned, §3's
  definition of MAJOR is untouched, and §4.1, §4.2 and §4.4 are unchanged.
- **§5.1's ground does not bite.** Its principle is dependability: an
  implementer could not have depended on the *absence* of a classification rule.
- **§1 item 1's ground does not bite.** No commitment is changed; one is added.
- **Nothing that conforms stops conforming**, and no implementation has anything
  to do.

That reasoning gives MINOR. It is a judgment made under an incomplete
framework — the last one, if this memo is accepted — and it is recorded as such.

For this release the level is academic: the memo travels inside 2.0 either way,
under §4. It is stated anyway, because a memo that skipped its own
classification because the answer did not matter would be teaching that the
declaration is a formality.

# 6. Effect on existing implementers

**None, and no reliance changes either.** No implementation has anything to do,
and nothing an implementer was entitled to rely on becomes something they are
not.

What changes is for the steward and for future proposals: a class of change that
was decided once by judgment now has a stated test, and the relationship between
the level of a change and the level of the release carrying it is written down
instead of assumed.

# 7. What this memo does not decide

- **Implementation conformance.** Whether a second class of conformance exists
  beside wire conformance — an SDK surface, a package's documented API — and who
  grants it. `SDK_SURFACE.md` declares itself *normative for implementations*,
  `GOVERNANCE.md` §6.1 names it while making the point that the normative set
  can grow, and the release manifest carries neither it nor `surface.json`. That
  is a question of authority and belongs in its own memo, which will be
  classified **under §4.5** once this one is in force.
- **What makes an artifact normative, and how it enters a release.** Related to
  the above and not the same question. A document that is normative and outside
  the published release is normative in a way nobody can verify.
- **Anything about the wire.** This memo adds no field, changes no schema, and
  imposes nothing on any producer or consumer.

# 8. Proposed incorporation

§3 and §4 of this memo as a new subsection `GOVERNANCE.md` §4.5, titled
*Changes to this policy and to the guarantees it defines*, placed after §4.4,
with the release-level rule as its closing paragraphs.

§4.1 through §4.4 are unchanged. This adds a domain they did not cover and
overrides none of them.

# Author

G. Garza, Wertek AI, Inc. — steward of the Industrial Asset Event Standard.
