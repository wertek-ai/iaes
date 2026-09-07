```
IAES                                                        G. Garza
Request for Comments: 000                                   Wertek AI
Category: Process                                    September 2026
ISSN: N/A

        Governance Bootstrap and Ratification of IAES 1.4
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. What governs is
> the specification, the schemas and `GOVERNANCE.md` as released. See
> `GOVERNANCE.md` §6.1.

This document records how the IAES change process came into being, and
ratifies the changes that were made while establishing it. It is a
Process document: it defines no wire format and changes no schema.
Distribution of this memo is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI. This document is made available under
the Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

IAES 1.4 published `GOVERNANCE.md`, which requires that changes to the
standard be proposed as numbered RFCs. IAES 1.4 itself did not go
through that process — it could not have, because the process did not
exist until 1.4 created it.

This memo names that gap rather than leaving it implicit, ratifies the
1.4 changes retroactively, and states plainly that it is the last time
a normative change to IAES will reach a release without an RFC.

# 1. The bootstrap problem

A change process cannot govern the change that creates it. When 1.4
made governance normative, every change in that same release had
already been made. Treating 1.4 as invalid for that reason would be
absurd; pretending the gap does not exist would be worse, because the
process is published and a reader can check.

So it is recorded here.

# 2. What IAES 1.4 changed

Ratified by this memo:

1. **Governance and compatibility policy became normative.**
   Stewardship, BACKWARD as the default compatibility mode, a 24-month
   support window, canonical and resolvable schema identity versioned
   by URI, and an RFC-based change process.

2. **Scope boundaries were made explicit.** IAES defines no asset
   hierarchy, no equipment catalog and no commercial terms. These are
   commitments, not preferences.

3. **Schema identity was corrected.** The eight schemas declared `$id`
   under a host that had never resolved. They now declare a base that
   is served. The former base is permanently reserved and will not be
   reassigned.

4. **`dataschema` was added** to the envelope: the canonical URI of the
   schema a payload was written against, derivable from `event_type`.
   Optional and additive.

5. **`event_type` was opened** from a closed enumeration of seven
   values to a dot-notation pattern, resolving a contradiction in which
   the same document ordered consumers to tolerate values that no
   producer could emit. Widening, therefore backward compatible.

No schema content changed in 1.4 beyond items 3 and 5.

# 3. What this memo does not do

This memo does not repair the defects found while auditing 1.4 for
publication. Those are the subject of the IAES 1.5 stabilization RFC
and are listed here only so that the record of 1.4 is honest about
what it does and does not contain:

- The specification's severity vocabulary is defined in three mutually
  incompatible ways across the specification, its own table, and
  RFC-001.
- `correlation_id` is REQUIRED in the envelope schema and declared
  OPTIONAL in RFC-001 §3.2.4.
- Six enumerations are closed that cannot be shown to be exhaustive.
- `content_hash` is not reproducible across implementations, because
  the two SDKs canonicalize differently.
- External normative references do not identify the edition they
  depend on.

# 4. Consequences, effective immediately

1. **Every normative change to IAES is proposed as an RFC before it
   reaches a release.** A single RFC may carry a coherent set of
   changes; the requirement is public reasoning and traceability, not
   paperwork per field.

2. **An incorporated RFC ceases to be normative authority.** Once its
   changes are merged into the specification and the schemas, an RFC
   answers *why a decision was made*, not *how IAES behaves*. This is
   not a stylistic preference: RFC-001 and the envelope schema
   currently disagree about whether `correlation_id` is required, and
   two simultaneous authorities is how that happens.

3. **A specification release is an indivisible object**: the
   specification, the governance document, the schemas, the
   conformance corpus and the manifest, published under one tag with
   one DOI. Implementation releases — the SDKs and node packages —
   declare which specification release they implement and do not carry
   a specification or a DOI of their own.

# 5. Ratification

The changes listed in Section 2 are ratified as IAES 1.4.

RFC-001 is retained as the historical record of IAES 1.3. Where it
disagrees with the current specification or schemas, the specification
and schemas govern.

# Author

G. Garza, Wertek AI — steward of the Industrial Asset Event Standard.
