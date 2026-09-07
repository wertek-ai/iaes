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

**State: Draft**, per `GOVERNANCE.md` §6. Distribution is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI, Inc. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

`GOVERNANCE.md` §3 says MAJOR is *anything that can break an existing producer
or consumer*. §4.2 operationalises that, and all five of its criteria are
shaped like schema changes. So a change that alters what a producer must **do**
— while altering no schema — has a category and no test.

This memo supplies the test. It classifies a change to an obligation by asking
what happens to an implementation **at the version it declares**, and it draws
one distinction that decides most cases: whether the new obligation *supplies*
a meaning the standard had left unstated, or *changes* one the standard had
already given.

# 1. What raised it

A drafted change would oblige a producer to omit an optional field it was not
given, rather than substitute a value. Measured against §4.2, it is none of the
five: it makes no optional field required, removes and renames nothing, narrows
no constraint, changes no unit, moves no `$id`. Every schema is byte-identical
before and after.

Reading it MINOR because nothing stops validating uses a test §4.2 does not
offer. Reading it MAJOR by analogy invents one. The gap is worth closing before
it is worked around, because every future decision of this shape hits it.

# 2. The mistake to avoid

The tempting rule is: *a new obligation makes a previously conforming producer
non-conforming, therefore MAJOR.*

It proves too much. Every new obligation does that, at the new version. Under
that rule MINOR could never carry a MUST, and the only compatible change would
be one nobody has to implement — which is not a compatibility policy, it is a
freeze.

The error is the frame. Conformance is not a property an implementation has in
the abstract; it is a property it has **against a version it declares**. An
implementation that declares 1.4 is measured against 1.4 for as long as 1.4 is
published, and `GOVERNANCE.md` §4.3 keeps that at least 24 months.

# 3. The criterion

> **[TEXT]** A change that adds or alters an obligation on a producer or a
> consumer, and changes no schema, is classified by applying the three tests
> below in order. The first that answers, decides.
>
> **T1 — Does data that was valid become invalid?**
> If yes: **MAJOR**. This is §4.2's territory and it governs unchanged.
>
> **T2 — Does an existing field's meaning change for events already on the
> wire?** A consumer that correctly followed version *N* would now misread an
> event produced under *N*. If yes: **MAJOR**.
>
> Meaning is *changed* only where the previous version stated one. Where the
> previous version left it unstated, the new version **supplies** a meaning,
> and supplying is not changing: no implementation was following a rule, so
> none is contradicted.
>
> **T3 — Does an implementation that declares version *N* stop conforming to
> *N*?**
> If yes: **MAJOR**. If it conforms to *N* and must change only in order to
> declare *N+1*: **MINOR**.
>
> An obligation that only restates what the existing normative text already
> required is **PATCH**, per §3.

Three notes on why it is shaped this way.

**T2 before T3.** A meaning change can leave every declared-version claim
intact and still break a consumer silently, which is the worst failure this
policy exists to prevent. It is asked before the cheaper question.

**T3 states the frame explicitly** rather than leaving it to be assumed. It is
the test that most often gets answered against the newest version by reflex,
and answering it that way produces §2's freeze.

**The tests are ordered and terminating**, so two readers applying them to the
same change reach the same answer. A checklist that has to be weighed as a
whole is not a criterion; it is an invitation to argue.

# 4. Applying it to the case in §1

- **T1** — no. Every 1.4 payload validates unchanged.
- **T2** — the previous version stated no meaning for an absent optional field.
  A consumer that defaulted an absent `anomaly_score` to `0.0` was filling a
  gap, not following a rule. The new obligation **supplies** the meaning. No.
- **T3** — a producer that declares 1.4 and substitutes still conforms to 1.4.
  It must stop only in order to declare 1.5.

**MINOR.**

The answer matters less than that it was reached by a stated test rather than
by whichever reading was convenient.

# 5. What this memo does not decide

- **Whether a second class of conformance exists** beside wire conformance —
  an SDK surface, a package's documented API — and who would grant it. The
  tests above are written for obligations on producers and consumers of
  events. Extending them elsewhere requires deciding that question first.
- **Anything about `format`.** Whether the specification's prose promises more
  than the schemas assert is a separate finding with its own remedy, and that
  remedy is a narrowing change under §4.2 — so it needs this criterion decided
  before it can be discussed, not the other way round.
- **Retroactive reclassification.** Releases already published keep the
  classification they were published with.

# 6. Proposed incorporation

If accepted, §3 as a new subsection of `GOVERNANCE.md` §4, numbered §4.4, with
a pointer from §4.2 saying that criteria for changes to obligations are found
there. §4.1 and §4.2 are unchanged: this adds a case they did not cover and
overrides neither.

The general statement, which is the part worth keeping if the rest is revised:

> A compatibility policy is not complete if it only classifies changes to the
> **representation**. It must also classify changes to the **obligations** of
> those who produce and consume that representation.

# Author

G. Garza, Wertek AI, Inc. — steward of the Industrial Asset Event Standard.
