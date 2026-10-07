# Conformance cases

One set of cases, run by every IAES implementation in this repository: the
Python SDK, the TypeScript SDK, the Node-RED nodes and the n8n nodes. If two
implementations give different answers for the same event, one of their CI
jobs fails.

## Why this exists

IAES has one specification and four implementations, and until these cases
each implementation re-wrote the rules by hand. Measured on 2026-10-06, that
is how they came to disagree:

- Node-RED accepted `spec_version: "205"` and Python rejected it.
- n8n's strict mode kept its own list of required fields, without
  `asset.hierarchy` and without three fields the schemas require.
- Node-RED rejected events with a non-UUID `event_id` that every other
  validator accepts.
- Python and TypeScript computed different `content_hash` values for six of
  eleven payloads.

Agreement between implementations is now something CI measures.

## Two verdicts

The specification asks two separate questions (IAES_SPEC.md, "An event can be
schema-valid and non-conforming"), and every case answers both.

| Verdict | Question | Who answers it |
|---|---|---|
| `schema_valid` | Do the published schemas accept this event? | `validate` in each SDK; the Node-RED and n8n nodes call the TypeScript SDK's |
| `conforming` | Does it also meet what the specification requires and the schemas only annotate? | `find_nonconformities` / `findNonconformities` |

The second exists because in 2.x the schemas declare `uuid`, `date-time`,
`date` and `uri` with `format`, which JSON Schema Draft 2020-12 treats as an
annotation, while the specification makes RFC 4122, RFC 3339 (in UTC) and
RFC 3986 normative for those fields. Making `format` binding in the schemas is
a narrowing change (GOVERNANCE.md §4.2) and is not available inside 2.x.

**Decision recorded here (2026-10-06):** the default answer of every validator
is `schema_valid`. A validator stricter than the schema by default makes two
readers disagree about the same bytes, which is the defect this suite exists
to prevent. Nonconforming fields are always reported; the Node-RED and n8n
nodes reject them only in **Strict** mode. A Node-RED node saved before the
Strict option existed keeps rejecting them, so that updating the package does
not change what a deployed flow accepts.

`find_nonconformities` keeps no list of fields: it reads the `format`
annotations from the schemas each package ships.

## Files

| File | What it holds |
|---|---|
| `validation.json` | Events with their expected `schema_valid`, `conforming` and `nonconforming_fields`. Most declare 2.0, which a 2.1 reader still reads; the `asset.state` cases declare 2.1, where the type exists |
| `content_hash.json` | `data` payloads with the canonical bytes and the `content_hash` each implementation must produce |

Both are **generated** by `tools/build_conformance_cases.py`; edit the
generator, never the JSON. `tests/test_conformance.py` fails if they are stale.

The expected values are written in the generator literally, from the
specification and the schemas. They are never computed by calling an
implementation: a suite whose answers come from the code it judges cannot
fail. The only thing computed is the SHA-256 of a canonical string that is
itself written out by hand.

## `content_hash`: two rules, by declared version

The rule follows the `spec_version` the event declares (IAES-RFC-011, accepted
in 2.1):

- **2.0 and earlier** keep the 2.0 computation. `agreed` cases must produce exactly
  the recorded bytes in every implementation. `divergent_2_0` cases record what each
  2.0 implementation produces, because they disagree: non-ASCII text, characters
  outside the BMP, integer-like keys, small and large exponents, and key order
  outside the BMP. The runner checks each implementation against its own value, so
  the divergence stays measured, and frozen: a 2.0 event keeps its 2.0 hash.
- **2.1 and later** hash the UTF-8 bytes of the RFC 8785 (JCS) serialisation. Every
  case carries `jcs` (canonical string and hash), the same in every implementation;
  `jcs_only` cases add RFC 8785's own example and the boundaries of the number form.

## Where each implementation runs the cases

| Implementation | Runner |
|---|---|
| Python SDK | `tests/test_conformance.py` |
| TypeScript SDK | `npm/test/conformance.test.js` |
| Node-RED nodes | `node-red/test/conformance.test.js` (both modes, plus a node saved before Strict existed) |
| n8n nodes | `n8n-nodes/test/conformance.test.js` (both modes) |

## Adding a case

1. Add it to `tools/build_conformance_cases.py`, with the expected verdicts
   taken from the specification and the schemas, not from running a validator.
2. Run `python tools/build_conformance_cases.py`.
3. Run the four runners. If one disagrees, decide which side is wrong before
   changing anything: the case, or the implementation.

## Contract

```
CONTRACT      conformance cases for IAES 2.x validators and content_hash
INPUT         conformance/validation.json, conformance/content_hash.json (generated)
OUTPUT        for each validation case: schema_valid (bool), conforming (bool),
              nonconforming_fields (sorted dotted paths, empty when the schema rejects the event)
              for each hash case: canonical string and content_hash, either agreed or per implementation
RULES         · the default verdict of every validator is schema_valid
              · a nonconforming field is reported, and rejected only in strict mode
              · find_nonconformities reads the schemas' `format` annotations; it keeps no field list
              · a crash (anything other than a validation error) is a failure, never a verdict
DO NOT INFER  · that a schema-valid event conforms
              · that two implementations produce the same content_hash for a 2.0 event with non-ASCII
                text, integer-like keys or exponents (see divergent_2_0); from 2.1 they do (jcs)
SOURCE        tools/build_conformance_cases.py; expected values written by hand from IAES_SPEC.md and schema/
```
