```
IAES                                                        G. Garza
Request for Comments: 009                                   Wertek AI
Category: Standards Track                            September 2026
ISSN: N/A

    Appendix C Cites the Wrong Part, and Still Claims a Mapping
                     2.0 Withdrew
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

**State: Draft**, per `GOVERNANCE.md` §6.
**Compatibility: MINOR · §4.5 R2. Target version: IAES 2.1.** Distribution is
unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI, Inc. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

`IAES_SPEC.md` Appendix C contradicts itself forty-two lines apart. Its header
records that the ISO 13374-2 attribution was withdrawn in 2.0 because the
correspondence was never verified; its closing section publishes a six-row
correspondence against that same part.

Measured while writing it: **the part number is also wrong.** The six-block
model is defined in ISO 13374-**1**, not -2, and the document that says so is
one the editor holds.

**2.0 stays as published.** `GOVERNANCE.md` §8 item 1 forbids editing a
released version and nothing here tries. This decides what 2.1 carries.

# Table of Contents

    1. The contradiction, measured
    2. The part number, and how it was checked
    3. Why buying ISO 13374-2 would not have helped
    4. What changes
    5. What this memo does not decide
    6. Compatibility level of this change
    7. Effect on existing implementers
    8. Proposed incorporation

# 1. The contradiction, measured

Both statements are in `IAES_SPEC.md`, in Appendix C, in the release tagged
`spec-v2.0`:

```
line 720   The `iso_13374_status` field on `asset.health` carries a health
           status level from IAES's own vocabulary. The attribution to
           ISO 13374-2 was withdrawn in 2.0: the citation did not identify a
           part, and the correspondence was never verified against the
           document.

line 762   IAES events map to the ISO 13374-2 processing blocks:
           [six-row table assigning each block to an event type]
```

They name the same part. The first says the correspondence was never verified
against the document; the second publishes a six-row correspondence against
that document.

`## References` supplies the reason the first one is right:

> The ISO 13374 entries say *series* rather than a part on purpose. […] the
> editor holds only ISO 13374-4. A citation that does not identify a document
> cannot be checked.

**A mapping cannot have been verified against a part nobody has.** The whole
reason 2.0 writes *ISO 13374 series* everywhere is that the parts were not
separable from the evidence available — and the appendix drops that discipline
exactly where it gets specific.

This is the fourth instance in this release cycle of one pattern: a correction
applied where it was discussed and not where the copy lived. `GOVERNANCE.md`
§1.1's exemption claim and §6.1's `SDK_SURFACE.md` example were two others,
both caught by `IAES-RFC-007` §3.1.

# 2. The part number, and how it was checked

`ISO 13374-4:2015`, which the editor holds, cites its sibling parts. Two of its
figure captions settle the question:

> **Figure 2 — Data processing block diagram (from ISO 13374-1:2003)**
>
> As specified in ISO 13374-1, an open CM&D processing architecture
> specification shall utilize the processing architecture shown in Figure 2.

and

> **Figure 1 — CM&D information architecture layers (from ISO 13374-2:2007)**

> ISO 13374-2 provides greater details into data processing methodology and
> requirements […]

**The six-block processing model is ISO 13374-1. ISO 13374-2 is a five-layer
information architecture.** They are different figures, in different parts, with
different subjects and a different number of elements.

So Appendix C does not merely publish an unverified correspondence. It
attributes a model to a part that does not contain it.

# 3. Why buying ISO 13374-2 would not have helped

The obvious repair — buy the cited part and verify the six rows — was
considered and is wrong, and the measurement above is why: the part would not
contain the model. Purchasing `ISO 13374-2:2007` would have confirmed only that
the citation was misdirected.

If the correspondence is ever to be claimed as verified, the document to
acquire is `ISO 13374-1:2003`.

This is the second time in this project that opening a document already held
answered a question that appeared to require buying another one.

# 4. What changes

Appendix C's closing section keeps its table and stops claiming a verified
correspondence. The table has teaching value for a reader arriving from
condition monitoring, and nothing about it is dishonest once it says where the
model comes from and how far the check went.

**Current:**

> ### ISO 13374 series 6-Block Processing Model
>
> IAES events map to the ISO 13374-2 processing blocks:

**Proposed:**

> ### The ISO 13374-1 six-block processing model
>
> The six-block processing model is defined in ISO 13374-1:2003. This is
> recorded here on the authority of ISO 13374-4:2015, which reproduces the
> block diagram and captions it *from ISO 13374-1:2003*; the editor holds
> ISO 13374-4 and does not hold ISO 13374-1.
>
> The table below places IAES event types against those blocks as an aid to
> readers who already work with the model. It is **not** a verified
> correspondence: the block definitions have not been read in their own
> document. IAES asserts nothing about ISO 13374 conformance, and no field's
> meaning depends on this table.

The rows are unchanged. The sentence already below the table — *IAES is an
event standard, not a processing pipeline* — is kept and is now consistent with
what precedes it.

The header at line 720 is corrected in one respect only: it names ISO 13374-2
as the withdrawn attribution, which is where the field's *values* were
attributed. That statement is about the status vocabulary and stays true. No
change.

# 5. What this memo does not decide

- **Whether to acquire ISO 13374-1.** If it is acquired and the six rows are
  read against it, the disclaimer can be withdrawn by a later memo. That is a
  purchase decision, not a specification decision.
- **Whether Appendix C should exist at all.** It is useful and it is honest
  once this change lands.
- **Anything about 2.0.** It stays exactly as published, and the `/schema/v2/`
  URIs are untouched — this changes prose, not a schema.

# 6. Compatibility level of this change

**MINOR, under `GOVERNANCE.md` §4.5 R2.** It changes how a normative annotation
is classified and disclosed. It reduces no obligation and adds none: nothing
required a producer or consumer to do anything on the strength of that table,
and §4's own References entry already records ISO 13374 series as *not
normative for meaning*.

§4.5 R2's guard applies and is satisfied: this does not relabel a narrowing as
a classification. Nothing a producer may emit changes.

# 7. Effect on existing implementers

**None.** No schema changes, no field changes meaning, no URI moves. A
consumer that reads `iso_13374_status` reads the same seven values it read in
2.0, from IAES's own vocabulary, as 2.0 already stated.

What changes is what a reader is told about where a table came from.

# 8. Proposed incorporation

1. **`IAES_SPEC.md` Appendix C**, closing section — heading and lead paragraph
   replaced per §4. Table rows unchanged.
2. **`IAES_SPEC.md` version history** — the 2.1 row records the correction.
3. **No other artifact changes.** `references/registry.json` already carries
   `ISO-13374-series`; this memo adds no reference and removes none.

# Author

G. Garza, Wertek AI, Inc. — steward of the Industrial Asset Event Standard.
