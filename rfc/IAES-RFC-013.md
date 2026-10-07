```
IAES                                                        G. Garza
Request for Comments: 013                                   Wertek AI
Category: Process                                      October 2026
ISSN: N/A

        A Draft Lives in Its Pull Request Until It Reaches Review
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

**State: Draft**, per `GOVERNANCE.md` §6. Open for comment. Following its own
rule, this memo lives in its pull request and does not enter `rfc/` on the
default branch until it reaches Review.
**Compatibility: MINOR**, by test R3 of `GOVERNANCE.md` §4.5 (§4).
**Target version: none stated yet.** Distribution is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

`GOVERNANCE.md` §6 defines the states of an RFC but not where a memo lives in
each of them. A Draft merged to the default branch for comment sits next to the
accepted memos and is read, packaged and cited as if it were one of them. This
memo proposes one rule: a Draft lives in its pull request; it enters `rfc/` on
the default branch when it moves to Review, or when it is closed as Rejected or
Superseded, so that the reason stays in the repository as §6 already requires.

# 1. The problem, measured

On 2026-10-06 `rfc/IAES-RFC-010.md` was merged to `main` as a Draft, so that it
could be commented on. Within the same day:

- the release manifest (`tools/build_release_manifest.py`) took every file in
  `rfc/` as the rationale of a release, so the next specification release would
  have shipped a Draft as part of its rationale. The tool had to learn to read
  the `State` line and leave non-Accepted memos out (wertek-ai/iaes#61, hardened
  in #65);
- an adversarial review found the Draft's design defects (it would have dropped
  repeated trips as duplicates, and one of its fields was MAJOR), while the
  memo already sat on `main` beside accepted ones.

Nothing was published wrongly: the manifest was fixed before any release. But
the defect was structural. The repository's default branch is what readers,
tools and citations take as the state of the standard, and a Draft there is
indistinguishable from an accepted memo unless every reader parses its State.

# 2. What the states already say

| State | Where the memo lives under this proposal |
|---|---|
| Draft | its pull request only |
| Review | `rfc/` on the default branch (the steward accepted it for consideration and stated a target) |
| Accepted | `rfc/` on the default branch, as rationale of the release that carries it |
| Rejected | `rfc/` on the default branch, with its written reason (§6: "The reason stays in the repository") |
| Superseded | `rfc/` on the default branch, naming its successor |

The rule follows the existing meaning of each state; it does not add a state.

# 3. The proposed change

Add to `GOVERNANCE.md` §6, after the table of states:

> **Where a memo lives.** A Draft lives in its pull request and is not merged
> to the default branch. It is merged when it moves to Review, or when it is
> closed as Rejected or Superseded, with its state and, for a closed memo, its
> reason. A Draft found on the default branch is moved back to a pull request
> or advanced to Review by the steward; it is never left there as a Draft.

# 4. Compatibility level

The change is to the process, with no event in it, so `GOVERNANCE.md` §4.5
classifies it.

- **R1 (reduction).** No guarantee given to implementers is removed or
  narrowed: implementers rely on released normative artifacts, and an RFC is
  not one (§6.1). R1 does not answer.
- **R2 (classification only).** It does not concern how changes are
  classified. R2 does not answer.
- **R3 (addition).** It adds an obligation of the steward (where memos live,
  and what to do with a Draft found on the default branch), reducing nothing.
  **MINOR.**

# 5. Effect on existing implementers

None on the wire, the schemas or the SDKs. For contributors: open a Draft as a
pull request and leave it there until the steward moves it to Review.

For the repository as of this memo: RFC-010, merged as a Draft on 2026-10-06,
was moved to Review on 2026-10-07 (wertek-ai/iaes#67), so no Draft remains on
`main`. RFC-012 was merged as Rejected, with its reason (wertek-ai/iaes#58).

# 6. Worked example

A contributor proposes a new memo and opens a pull request that adds it to
`rfc/` with `**State: Draft**`. Comments happen on the pull
request. The steward states a target version and moves it to Review: the State
line changes in the same pull request, and only then is it merged. Had the
steward rejected it instead, the State line would say Rejected, a reason
section would be added, and the memo would be merged so the reason stays in the
repository.

# 7. Proposed incorporation

When Accepted, in the same change: the paragraph of §3 in `GOVERNANCE.md` §6,
and a line in `CONTRIBUTING.md` where it explains how to open an RFC.

# 8. What this memo does not decide

- How long a Draft may stay open, or when a stale Draft is closed.
- Who may move a memo to Review (the steward, per §6, unchanged).

# Author

Gilberto Garza, Wertek AI -- steward of IAES.
