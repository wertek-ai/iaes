# Integrating IAES — for a person, or an agent working for one

> **Not normative.** `IAES_SPEC.md` and `GOVERNANCE.md` govern, and where this
> file and an artifact disagree, **the artifact governs and this file is the
> defect** (`AGENTS.md`, "Where authority lives"). This file points; it does not
> restate rules.
>
> **Who this is for.** Someone who needs to connect a system to IAES — a
> producer, a consumer, or an adapter between two systems — and who may hand
> the reading and the first implementation to a coding agent. If you are
> *changing this repository*, read `AGENTS.md` and `CONTRIBUTING.md` instead.

## What this file does not promise

Say this to whoever reviews the result, because an agent will not volunteer it.

- **A passing validator is not conformance.** The schemas check shape.
  `IAES_SPEC.md`, section *An event can be schema-valid and non-conforming*,
  records that a `timestamp` of `"banana"`, an `event_id` of `"no-uuid"` and a
  `dataschema` that is not a URI all pass the schema and all violate the
  specification. Green from `validate` is necessary, not sufficient. The list
  of what it cannot see is below.
- **A human still reviews.** Nothing here makes generated code correct. It
  gives the generator something to check against and the reviewer something to
  check with.
- **This is not a guide for any particular target system.** `IAES_SPEC.md`,
  section *System Compatibility*, names how IAES maps to SAP PM, MaintainX,
  Fracttal and others in one line each. The repository's own mapping file,
  `mapping/v1/target-systems.draft.json`, is a **draft**. An adapter to a
  target system is therefore your decision, not the standard's.

## Read, in this order

| To learn | Read |
|---|---|
| What an event is and what a producer or consumer MUST do | `IAES_SPEC.md` — *Common Envelope*, *Producer Guidelines*, *Consumer Guidelines* |
| Which event type fits | `IAES_SPEC.md` — *Event Type Usage Guide* (it also says when **not** to use each) |
| What IAES deliberately does not define | `GOVERNANCE.md` §1, and `IAES_PHILOSOPHY.md` |
| What may change between versions | `GOVERNANCE.md` §4 |
| The exact shape of each payload | `schema/*.schema.json` |
| A worked, executable story in your runtime | `scenarios/` — Python, TypeScript, Node-RED, n8n, Ignition, all checked against `scenarios/fixture.json` |
| What a library exposes | `surface.json`; what each one offers today, `implementations.json` |

Use the scenario for your runtime as the starting point rather than writing the
first event from the spec. It is the one thing here that is executed by CI.

## The rule that matters most

**Do not infer semantics the specification does not state.**

When the specification is silent — how a severity maps to a target system's
priority, what a field means in your plant, which asset id to use — **stop and
report the gap**; do not choose a value and move on. Two cases that are
already settled, so you do not have to guess:

- A field you were not given is **omitted**, never filled. `IAES_SPEC.md`,
  *Producer Guidelines*, recommended behaviour 3: `anomaly_score: 0.0` for a
  score nobody computed is indistinguishable from a measured zero.
- `event_type` and `measurement_type` are **open**. Use a published type where
  one fits; define your own only in a namespace you control and omit
  `dataschema` for it (*Producer Guidelines*, recommended behaviour 4 and 5).
  Do not close either list in your code.

## Checking your own work

Run the validator, then check by hand what it cannot see.

```bash
pip install "iaes[validate]"        # validate() needs the extra
```

```python
from iaes import validate
validate(event_dict)                # raises on a schema violation
```

The TypeScript SDK exposes the same word, `validate` (`surface.json`,
`naming`). The scenarios show both in use.

**What `validate` does not check — you must.** Each is stated in
`IAES_SPEC.md`, *Required behavior* (producers) or *References*:

1. `timestamp` is RFC 3339 and UTC, with a timezone designator.
2. `event_id`, `correlation_id` and `source_event_id` are UUIDs.
3. `dataschema`, if present, is a URI, and for a published type is
   `https://iaes.dev/schema/v2/<event_type>`; a custom type omits it.
4. Events that belong to one flow share one `correlation_id`; an event caused
   by another carries that event's `event_id` as `source_event_id`.
5. No optional field carries a value you were not given.
6. A consumer tolerates unknown fields and unknown `event_type` values instead
   of erroring (*Consumer Guidelines*, required behaviour 1 and 2).

If your integration has a consumer side, also run the checks in
`CONTRIBUTING.md`, "Running the tests", for the runtime you used.

## What to tell the person who asked

A short report is better than a confident one. State:

- which files you read and which scenario you started from;
- what you ran, and what it printed;
- every place the specification was silent and what you did about it;
- anything you could not verify — for example, the behaviour of the target
  system, which this repository does not test.

## An example request

> Use this repository as the canonical event contract. My gateway produces
> `{device, vibration_mm_s, temperature_c, timestamp}`. Build the adapter,
> keep provenance, validate every event with the repository's validator, and
> check the conformance points listed in `INTEGRATING_WITH_AGENTS.md` that the
> validator does not. Do not invent semantics the specification does not state;
> list the gaps you found instead.

This is an example of the shape of a request, not a measured recipe. Whether
agents given it produce conforming adapters is being tested, and the result,
whichever way it falls, will be recorded in this repository.
