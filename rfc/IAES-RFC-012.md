```
IAES                                                        G. Garza
Request for Comments: 012                                   Wertek AI
Category: Standards Track                              October 2026
ISSN: N/A

        What a Major's Schema URI Serves When a Minor Is Released
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

**State: Draft**, per `GOVERNANCE.md` §6. Open for comment.
**Compatibility: MINOR** if the steward confirms the R1 analysis in §5;
otherwise MAJOR. **Target version: none stated yet.** Distribution is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

`GOVERNANCE.md` §5 versions schemas by URI per **major**: every 2.x release
shares `https://iaes.dev/schema/v2/<type>`. §8 item 1 says published versions
are "never edited in place" and "always resolvable at their URI and DOI". Read
together, they leave a minor release unable to change any byte of an existing
schema -- not a new optional field, not an added example -- without breaking
one of the two. The first minor after 2.0 (`rfc/IAES-RFC-010.md` proposes one
optional field and one added example) needs the answer. This memo proposes it:
the major's URI serves the latest minor of that major, and each release's exact
bytes stay resolvable at a per-release path, at the release tag and at the DOI.

# Table of Contents

    1. The problem
    2. What already assumes an answer
    3. The proposed rule
    4. Worked example
    5. Compatibility level of this change
    6. Effect on existing implementers
    7. Proposed incorporation
    8. Open questions

# 1. The problem

- `GOVERNANCE.md` §5: "a MAJOR version publishes under a distinct path". A minor
  therefore publishes under the same path as its major.
- `GOVERNANCE.md` §8 item 1: "Published versions are never edited in place,
  never unpublished, and always resolvable at their URI and DOI."
- `GOVERNANCE.md` §4.1: adding an optional field is MINOR.

A 2.1 that adds an optional field to `maintenance.completion` changes the bytes
served at `https://iaes.dev/schema/v2/maintenance.completion`. Either that is an
in-place edit of 2.0 at its URI (against §8 item 1), or 2.1 cannot add the
field to that schema (against §4.1 in practice). Nothing in the normative text
says which.

# 2. What already assumes an answer

- The site's header rules for `/schema/v2/*` say a schema URI is "a fixed name
  whose content can change within a MINOR release" (iaes.dev `_headers`).
- The site serves each major from one release tag (`schema/SERVED.json`, v2 →
  `spec-v2.0`), with a note that it moves when a 2.x release ships.
- `rfc/IAES-RFC-008.md` decided that "a representation served under a major's
  URI stays that major's and is never regenerated from a later release" -- a
  rule across majors, which says nothing about minors within one. The rule it
  promised to add to `GOVERNANCE.md` §5 was not incorporated; this memo
  incorporates it together with its own.
- `tools/check_schema_compat.py` already enforces, on every pull request, that a
  change to a published schema is BACKWARD compatible or bumps the major.

So the practice already assumes "the major's URI serves the latest minor". It is
not written where an implementer can rely on it.

# 3. The proposed rule

Added to `GOVERNANCE.md` §5:

1. **A major's URI serves the latest release of that major.**
   `https://iaes.dev/schema/v2/<type>` serves the schema as released by the most
   recent `2.x`. Because every minor is BACKWARD compatible (§4, enforced by the
   compatibility guard), an event valid under any earlier `2.x` stays valid
   against what that URI serves.
2. **Every release's exact bytes stay resolvable**, at three places: a
   per-release path, `https://iaes.dev/schema/v2.<minor>/<type>`, which is never
   changed once published; the release tag in the repository; and the release
   DOI.
3. **A representation served under a major's URI stays that major's** and is
   never regenerated from a later major (RFC-008, incorporated here).

§8 item 1 is amended to read "always resolvable at their per-release URI and
DOI", with a pointer to §5.

# 4. Worked example

IAES 2.1 adds `active_repair_seconds` to `maintenance.completion`.

| URI | Serves after 2.1 |
|---|---|
| `https://iaes.dev/schema/v2/maintenance.completion` | the 2.1 schema (the `$id`, unchanged) |
| `https://iaes.dev/schema/v2.0/maintenance.completion` | the 2.0 bytes, exactly |
| `https://iaes.dev/schema/v2.1/maintenance.completion` | the 2.1 bytes, exactly |
| `https://iaes.dev/schema/v1/maintenance.completion` | the 1.x bytes, as today |

A consumer that validates a 2.0 event against the `$id` URI keeps getting the
same result: 2.1 only added an optional field. A consumer that needs the exact
2.0 bytes (to reproduce a validation, or for an audit) reads them at `/v2.0/`.

# 5. Compatibility level of this change

This changes the policy and §8, so `GOVERNANCE.md` §4.5 classifies it.

- **R1 (reduction).** What implementers were entitled to rely on: that a
  published release is resolvable at a URI and at its DOI, and that it is never
  edited. After this change, every release is resolvable at a URI that is never
  edited (the per-release path) and at its DOI; and the `$id` URI keeps
  returning a schema that validates every event the earlier release accepted.
  Nothing an implementer could do before becomes impossible. **The steward must
  confirm one reading:** that §8 item 1's "their URI" never meant the `$id` URI
  frozen at the first minor's bytes. If it did, the change narrows a guarantee
  and is MAJOR (R1).
- **R2 (classification only).** No.
- **R3 (addition).** The per-release paths add a guarantee and an obligation of
  the steward (to serve them). **MINOR.**

# 6. Effect on existing implementers

- **Producers and consumers:** none. `$id` values do not change; `dataschema`
  keeps pointing at the major's URI.
- **The website:** serves `/schema/v2.0/` from `spec-v2.0` before `/schema/v2/`
  moves to a later minor; its parity guard learns the per-release paths
  (immutable, like `/schema/v1/` today).
- **SDKs:** none; they ship their own copies.

# 7. Proposed incorporation

When Accepted, in the same change: `GOVERNANCE.md` §5 (the three rules of §3,
including RFC-008's) and §8 item 1 (the amended wording), and the version
history row in `IAES_SPEC.md`.

# 8. Open questions

1. **Path shape.** `/schema/v2.0/` or `/schema/2.0/`? The first reads next to
   `/schema/v2/`; the second reads like a version number.
2. **Backfill.** Should `/schema/v1.4/` and `/schema/v2.0/` be published as soon
   as this is accepted, so that every release since 1.4 has a per-release path?

# Author

Gilberto Garza, Wertek AI -- steward of IAES.
