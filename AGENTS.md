# Working in this repository

> For anyone changing this repository —a person or an agent. `CONTRIBUTING.md` says
> which door a change comes through and how to run the tests; this says how to
> work once you are inside. `IAES_PHILOSOPHY.md` says why the standard is
> shaped this way.
>
> **Not normative.** `IAES_SPEC.md` and `GOVERNANCE.md` govern.

## Where authority lives

| Question | Answer lives in |
|---|---|
| What must an event do? | `IAES_SPEC.md` |
| What may change, and how? | `GOVERNANCE.md` |
| Why was this decided? | `rfc/` — and an RFC is **not** authority for behaviour (`GOVERNANCE.md` §6.1) |
| What does a library have to expose? | `surface.json` |
| Which external documents may be cited? | `references/registry.json` |

Everything else — this file, `IAES_PHILOSOPHY.md`, `README.md`, `SDK_SURFACE.md`
— explains. When an explanation and an artifact disagree, **the artifact
governs**, and the explanation is the defect.

## The rules that were learned the expensive way

Each of these is here because it already failed, not because it sounded
prudent.

### A check that cannot run must fail explicitly

**A partial check may not report total success.**

The retired-key check on the website asked whether a key had ever been
declared, using git history. CI checks out shallow by default, so there was no
history, and it reported every key as never having existed — twenty invented
findings. Then the local clone turned out to be shallow too: the check had been
*passing* for the wrong reason, and a key retired beyond the horizon would have
been denounced as a name that never was.

The answer depended on clone depth, which is not a property of the truth.

So: detect the missing precondition, say so once, and do not answer. A silent
skip is how a check stops checking while staying green.

### Arm the guard at zero

Before trusting a new check, break the thing it watches and watch it go red —
in the environment that is meant to protect you, not only on your machine.

Arm the **negative control** too. A guard that fires on correct content is a
guard that gets switched off: the section check keys on anchors rather than
heading text precisely so a legitimate rename does not go red.

Arm from a **committed** baseline. Restoring with `git checkout -- .` reverts
to `HEAD` and destroys uncommitted work — that happened here, mid-session, to
the very sections being armed.

### Measure where the thing is

Before asserting that something does not exist, run a **positive control**:
find something you know is there, the same way. Absence found by the wrong
instrument is indistinguishable from absence.

Cases from this repository: a `curl` that reported four broken package links,
when the same `curl` got 403 from npm's home page; a case-sensitive grep that
found nothing while the text was in capitals; a substring test that reported a
section present because the word appeared elsewhere on the page.

### Anchor to structure, not to distance

A check that locates its subject by adjacency, by name, or by a window of bytes
breaks on the next edit and does so silently. Locate by AST, by element, by
anchor — by something the document itself asserts.

### A guard that states a property must execute it

`check_spec_sections.py` documented three properties and implemented two: the
third skipped and then did nothing with what it kept. Prose in a checker is not
a check, and it is more dangerous than no prose at all, because it is read as a
guarantee.

### The release governs

If the source reads oddly while you are reproducing it, **reproduce it**. Open
the correction as debt for the next version; do not improve it downstream. A
derived surface that silently disagrees with the release is worse than one that
faithfully carries a known wart.

Corollary: a past release's identifiers belong to its own version forever. A
sweep that migrates current content must not touch historical rows — that
failed here, on a version-history row whose URIs were rewritten forward.

### Cite; do not paraphrase

Explanations point at the artifact that carries the rule. A paraphrase drifts
from its source and then replaces it. `tools/check_citations.py` verifies that
every `§` reference in this repository names a section that exists.

## Before opening a pull request

```bash
python tools/check_citations.py          # every § names a real section
python tools/check_frontier.py           # the standard depends on nothing of ours
python tools/check_document_available.py # cited documents are identified
python -m pytest tests/ -q               # the specification's own tests
```

`CONTRIBUTING.md` has the full sequence, including the SDKs and the nodes.

A normative change additionally needs a decision under `GOVERNANCE.md` §6, and
`tools/check_release_accounting.py` proves at release time that no normative
change entered without one.

## What not to do

- **Do not edit a published release.** `GOVERNANCE.md` §8 forbids it, and the
  tags are the evidence.
- **Do not add a default that points at any vendor's infrastructure** — ours
  included. `GOVERNANCE.md` §1.1.
- **Do not close an open catalog** in an implementation. `event_type` and
  `measurement_type` are open, and both flow validators once re-closed them.
- **Do not grant conformance.** It is claimed and checked (`GOVERNANCE.md`
  §9.3).
- **Do not report a finding you have not reproduced.** Say what you measured,
  with what, and what would falsify it.
