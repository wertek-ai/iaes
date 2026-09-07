# Contributing to IAES

`GOVERNANCE.md` §6 says anyone may open an RFC. This file is how.

It does not restate the rules — `GOVERNANCE.md` is the authority on scope,
compatibility and the change process, and duplicating it would create a second
place to disagree with itself.

## Which door

**A change to the standard goes through an RFC.** That means anything that
changes what an event is or what a conforming implementation must do: a field,
a type, an enumeration value, a constraint, a required/optional decision, or
the meaning of any of them.

Write it as `rfc/IAES-RFC-NNN.md`, numbered after the highest that exists, and
open a pull request. The RFC states the problem, the proposed change, the
compatibility level under `GOVERNANCE.md` §4, the effect on existing
implementers, and at least one worked example. It starts in **Draft** and
nothing in it is in force until it is Accepted.

`rfc/IAES-RFC-002.md` is a reasonable one to copy the shape from.

**Everything else is an ordinary pull request:** documentation, examples,
tests, tooling, SDK internals, a broken link, a typo. If you are not sure which
door you are at, open an issue and ask — being wrong about it costs a comment.

## What is normative, and what is not

This distinction decides which door you are at, and it is not obvious from the
file names.

| | |
|---|---|
| `schema/*.schema.json` | **decides machine-validity of an event.** It is what a validator runs. |
| `IAES_SPEC.md` | normative prose. Governs semantics: what a field means and what a conforming implementation must do. |
| `rfc/*.md` | **rationale, not authority** — `rfc/IAES-RFC-000.md` §4, item 2. An incorporated RFC records why a decision was made; it does not make one. |
| `SDK_SURFACE.md`, `surface.json` | normative **for implementations**, not for the wire. What an SDK must expose to call itself an IAES SDK. Conformance is measured on the wire, so an SDK that exposes less is still producing valid events. |
| `GOVERNANCE.md` | **normative too.** The process, the scope boundaries and the compatibility policy. It declares commitments no schema could override: §1, item 2 excludes equipment catalogs by name, and a schema that closed one would be the defect. |
| everything else | tooling, examples, tests. |

None of the three outranks the others, and **they must not contradict one
another**. Where they do, the disagreement itself is the defect, and which one
gives way depends on which is wrong — that is a question for the pull request,
not a rule of precedence. The `correlation_id` divergence was found exactly
that way: three documents, one of them stale, and no amount of precedence
would have told you which.

Changing prose to match the schema is an ordinary pull request. Changing what
an event is, or what an implementation must do, is an RFC.

## Running the tests

Everything CI runs, you can run. There is nothing you need from us to do it.

```
# The specification, its guards, and the Python SDK
pip install -e ".[dev]"
PYTHONPATH=src python -m pytest tests/ -q

# The TypeScript SDK
cd npm && npm ci && npm run build && npm test

# The Node-RED nodes and the n8n nodes, against the local SDK
cd node-red && npm ci && npm test
cd n8n-nodes && npm ci && npm run build
```

Two guards run on every change and are worth knowing about before you are
surprised by them:

```
python tools/check_frontier.py                       # GOVERNANCE.md 1.1
python tools/check_schema_compat.py --baseline main  # GOVERNANCE.md 4
```

The first fails when the standard starts depending on its steward — a host, a
namespace or an operating model of ours in a schema, a default or required
behaviour. Naming Wertek in prose is fine; pointing at it in a value is not.

The second fails on a change that would break a consumer reading the old
schemas. It is the mechanical form of the compatibility policy, and it is
allowed to be wrong about your intention: if it fails and you believe the
change is compatible, say why in the pull request rather than working around
it.

## What a good change looks like here

- **A claim about the standard comes with the comparison that produced it.**
  Most defects found in this repository were found by comparing one artifact
  against another, not by reading one carefully.
- **A guard is armed before it is trusted.** A check that has never been seen
  to fail has not been shown to work. Break the thing on purpose, watch it go
  red, and put that in the pull request.
- **An exception is declared, not tolerated.** If something cannot be fixed
  now, say so in the file, with the reason and the version that resolves it.
  Several tests here fail when an exception has no reason attached.

## Reporting rather than fixing

An issue is a fine contribution. If you found something and do not want to
write the fix, say what you compared and what disagreed — that is the part
that is hard to reproduce later.

See [`SECURITY.md`](SECURITY.md) before opening an issue that involves a
vulnerability, or any data from a real installation.

## Licence

Contributions to this repository are made under the licence in
[`LICENSE`](LICENSE) (CC BY 4.0). The published SDKs carry their own licences,
stated in their package metadata.
