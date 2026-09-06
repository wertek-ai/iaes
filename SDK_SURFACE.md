# IAES SDK Surface

> **Status: normative for implementations, not for the wire.**
>
> This document does not change what an IAES event is. It says what an
> implementation that calls itself an IAES SDK must expose, so that somebody who
> has learned one has learned them all.
>
> The machine-readable form is [`surface.json`](surface.json), and
> [`tests/test_surface.py`](tests/test_surface.py) reads it. That sentence used
> to be here and was untrue: nothing read the file, so its declarations drifted
> until three of five were wrong in the file's own favour.

## Why this exists

Five platforms emit IAES events. None of them agreed with the others, because
nobody decided the surface — it accumulated, one first use case at a time.

The shape of the gaps says where the attention went. **Validation — literally
checking conformance — is missing from the TypeScript SDK, which is the one both
flow runtimes depend on.** Publishing, which is not part of this standard, is
everywhere.

The cost lands on the person this standard is for. An integrator who learns the
Python SDK and moves to TypeScript looks for `validate` and does not find it,
looks for `from_dict` and finds `fromJSON`, looks for `Client` and finds
`IaesClient`. Nothing there is wrong on its own. Together they mean the SDKs
have to be learned one at a time, which is the opposite of what a standard is
for.

## The rule

**The same word, in each language's convention. Never a different verb.**

`compute_content_hash` and `computeContentHash` are the same capability spelled
by two languages, and that is correct. `from_dict` and `fromJSON` are not: they
are different verbs, and a reader cannot tell whether they do the same thing
without opening both.

A capability that exists but cannot be reached idiomatically does not count.
Measured 2026-09-06: Python had `schema_uri_for` and did not export it from the
package root, while TypeScript exported `schemaUriFor` from its index — so
`from iaes import schema_uri_for` failed while the TypeScript equivalent worked.
Fixed rather than declared.

## What is standardised, and what is not

| standardised | left to the language |
|---|---|
| the **name** of each capability | the **container** the input arrives in |
| the **field names** — they are the schema's | the **shape of the call** |
| the **outputs**, and how failure looks | the **internals** |
| the **observable behaviour** | |

Internals are deliberately excluded. A standard that dictates how an
implementation is built inside stops being a data contract and becomes a
framework, and an internal method is not something a third party can conform to
because nobody outside can observe it. What *is* required of the inside is
behaviour: that the digest comes out the same, that a retransmission keeps its
identifier, that an unknown event type does not throw.

## The container is not the universal part — the field names are

Forcing one container everywhere would make the C++ binding worse rather than
more portable: a microcontroller has no business allocating a dynamic map of
strings when a struct will do. It stays homologous because the fields are
called the same thing.

| platform | idiomatic container |
|---|---|
| Python | dataclass with keyword arguments |
| TypeScript | typed object literal |
| C++ | `struct` |
| Node-RED, n8n | the fields of the edit dialog |

Every SDK offers **two doors to the same result**: the typed constructor for the
ordinary path, and construction **from a plain object** for when the data
already exists as JSON, or when the typed form is in the way.

## Flexibility, and where it does not belong

Extra fields are carried through, not stripped and not rejected. The
specification already requires consumers to tolerate fields they do not know;
producers should be as generous, or forward compatibility only works in one
direction.

Batches are lists **of events** — `publish([a, b, c])`. A list is never how
fields are passed. Positional fields make the order part of the contract, cost
you the ability to say which field was missing, and throw away the one thing
that is genuinely universal: the name. `units_qualifier` means the same in five
languages; "the fourth position" means nothing.

Omitting an optional field and passing null behave identically.

## Failure has to look the same, and today it does not

This is the part with the least attention and the most consequence. Python
raises `ValidationError`; TypeScript has `IaesClientError`; they do not do the
same thing. An integrator moving between them needs to know what a failure is:
what is raised, what a validator returns for an invalid event, and whether it
says **which field** failed.

An SDK reports a validation failure with the path of the offending field. "This
event is invalid" is not usable by somebody holding a hundred of them.

## Declaring a gap

An SDK that does not implement a capability **declares it**. A capability that
is simply absent is indistinguishable from one nobody thought of, and that is
how five platforms arrived at five different surfaces.

A declared gap is a legitimate state. A silent one is a defect. **An undeclared
gap that gets quietly filled is a defect in the other direction**, and the test
checks both.

## The capabilities

Names below are canonical. Each language spells them in its own convention.

| capability | what it does | notes |
|---|---|---|
| `build` (per event type) | constructs an event of that type | one per published type — seven today |
| `from_object` | constructs from a plain object | the flexible door |
| `validate` | checks an event against its published schema | reports the failing field's path |
| `compute_content_hash` | SHA-256 over canonical JSON, sorted keys, first 16 hex | must agree across languages |
| `schema_uri_for` | derives the schema URI from an event type | this is what `dataschema` carries |
| `route` | separates events by type | uses only the published vocabulary |
| *vocabulary* | the published enumerations | all ten, not the ones a first use case needed |

**`publish` is not on this list, on purpose.** Sending an event somewhere is not
yet part of this standard: IAES defines no transport, no endpoint contract and
no delivery negotiation, so there is nothing for a second implementation to
conform to. A function that sends is a client for a particular server, and it
belongs to that server's package. It becomes an IAES capability the day a
transport binding exists — not before.

## Where the five stand, measured 2026-09-06

| | build | from_object | validate | hash | schema_uri_for | route | vocabulary |
|---|---|---|---|---|---|---|---|
| **Python** | 7 / 7 | ✓ | ✓ | ✓ | ✓ | — | 10 / 10 |
| **TypeScript** | 7 / 7 | ✓ | **✗** | ✓ | ✓ | — | 10 / 10 |
| **Node-RED** | 3 / 7 | ✗ | ✓ | via SDK | ✗ | ✓ | 10 / 10 |
| **n8n** | 6 / 7 | ✗ | ✓ | via SDK | ✗ | ✗ | 10 / 10 |
| **C++** *(other repo)* | 2 / 7 | ✗ | ✗ | ✓ | ✗ | ✗ | 1 / 10 |

`route` is absent from Python and TypeScript and is **not** counted as a gap: a
library caller does that with a switch. It is required where the platform's
shape makes it meaningful, which is a flow runtime.

Two things this table made visible that were not in the file before:

- **Neither flow runtime emits `dataschema`**, although both depend on a
  TypeScript SDK that can derive it. The field is optional and additive, so
  nothing breaks — it is simply not being carried.
- **Node-RED ships an `iaes-sparkplug` node.** A protocol binding is useful and
  is not part of the surface every implementation must offer; it is listed under
  `not_capabilities` so that its absence elsewhere is not read as a gap.

## What is not checked here

The C++ runtime lives in
[wertek-ai/iaes-opta-runtime](https://github.com/wertek-ai/iaes-opta-runtime)
and its conformance runs in that repository's CI. `tests/test_surface.py` does
not verify its row. That is a real hole in this file's guarantee, said out loud
rather than left to be discovered.

---

*Machine-readable: [`surface.json`](surface.json). Checked by
[`tests/test_surface.py`](tests/test_surface.py). Boundary rules:
[`GOVERNANCE.md`](GOVERNANCE.md) §1.*
