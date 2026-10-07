```
IAES                                                        G. Garza
Request for Comments: 011                                   Wertek AI
Category: Standards Track                              October 2026
ISSN: N/A

        One Canonical Form for content_hash: Adopt RFC 8785 (JCS)
```

# Status of This Memo

> **Authority notice.** This RFC records a proposal and the reasoning behind
> it. It is **not** normative authority for how IAES behaves. The applicable
> normative artifacts, as released, govern IAES. See `GOVERNANCE.md` §6.1.

**State: Review**, per `GOVERNANCE.md` §6: accepted for consideration by the steward
on 2026-10-07. Still open for comment; it becomes Accepted only when its change is
incorporated (§8) in the release that carries it.
**Compatibility: MINOR**, by the tests of `GOVERNANCE.md` §4.4 (§5).
**Target version: 2.1.** Distribution is unlimited.

# Copyright Notice

Copyright (c) 2026 Wertek AI. This document is made available under the
Creative Commons Attribution 4.0 International License (CC BY 4.0).

# Abstract

`content_hash` is how IAES consumers detect duplicate events. The specification
says it is computed over "canonical JSON, sorted keys" and does not say what
canonical means. The two SDKs took different readings, and they disagree today
on any `data` payload that contains a non-ASCII character, a number outside a
narrow range, or a key that looks like an integer. This memo proposes that
canonical means **RFC 8785, the JSON Canonicalization Scheme (JCS)**: an
existing IETF specification that fixes how keys are ordered, how strings are
escaped and how numbers are written. Neither SDK follows it exactly today, so
every implementation changes.

# Table of Contents

    1. The problem, measured
    2. Why the specification lets both readings through
    3. The proposed change
    4. Why RFC 8785 rather than a rule of our own
    5. Compatibility level of this change
    6. Effect on existing implementers
    7. Worked example
    8. Proposed incorporation
    9. What this memo does not decide
    10. Open questions

# 1. The problem, measured

Measured on 2026-10-06 with the released 2.0.2 packages (`compute_content_hash`
in Python, `computeContentHash` in TypeScript), same `data`, side by side:

| `data` | Python | TypeScript | |
|---|---|---|---|
| `{"reason": "motor protection trip"}` | `0f6d98391542f00b` | `0f6d98391542f00b` | agree |
| `{"reason": "disparo de protección"}` | `8af73ebab2507204` | `35bfe554a215913c` | **differ** |
| `{"v": 0.1}` | `8ec9c466832e74ca` | `8ec9c466832e74ca` | agree |
| `{"v": 123456.789}` | `e1c86a6569ec9f9d` | `e1c86a6569ec9f9d` | agree |
| `{"v": 1e-7}` | `91f2443f2f247a30` | `3a28f15de586a90e` | **differ** |
| `{"v": 1.5e-5}` | `4df3acabdba004e7` | `7c56bd8bbfb403e3` | **differ** |
| `{"v": 2.5e21}` | `dbfa755576bd5c8c` | `7046c22c1149e655` | **differ** |

Three more cases, measured the same day while building the shared conformance
cases (wertek-ai/iaes#63, `content_hash.json`), show that the TypeScript SDK is
not JCS either:

| `data` | Python canonical | TypeScript canonical | JCS (RFC 8785) |
|---|---|---|---|
| `{"9":1,"10":2,"a":3}` | `{"10":2,"9":1,"a":3}` | `{"9":1,"10":2,"a":3}` | `{"10":2,"9":1,"a":3}` |
| keys U+E000 and U+1F600 | U+E000 first | U+1F600 first | U+1F600 first |
| `{"note":"🔧 wrench"}` | `🔧` escaped | UTF-8 | UTF-8 |

The causes are in the serialisers:

- **Strings.** Python's `json.dumps` escapes every non-ASCII character
  (`ó`); JavaScript's `JSON.stringify` writes it as UTF-8.
- **Numbers.** Python writes `1e-07` and `1.5e-05`; JavaScript writes `1e-7` and
  `0.000015`. Python's SDK turns whole floats into integers before hashing
  (`src/iaes/envelope.py`, `_normalize_for_hash`), so `2.5e21` becomes
  `2500000000000000000000`, while JavaScript writes `2.5e+21`.
- **Key order.** Python sorts keys by code point; RFC 8785 sorts by UTF-16 code
  unit, so they differ for keys outside the Basic Multilingual Plane. The
  TypeScript SDK sorts correctly but then builds a new object
  (`npm/src/envelope.ts`, `sortKeys`), and JavaScript enumerates integer-like
  keys first, in numeric order, whatever order they were inserted in. So
  `"10"` lands after `"9"`.

`tests/test_reference_scenarios.py` checks that every implementation agrees on
`content_hash`, and it passes, because the reference story is ASCII with
ordinary numbers. A plant writing Spanish, Portuguese or Japanese text, or
reporting a small quantity, gets a different hash from each SDK. Two producers of
the same event -- or one producer and one consumer that recomputes -- then fail
to recognise a duplicate.

# 2. Why the specification lets both readings through

`IAES_SPEC.md`, *Producers*, item 6: "the first 16 characters of the SHA-256 hex
digest of the serialized `data` payload (canonical JSON, sorted keys)". It names
neither the bytes that are hashed (which encoding) nor the serialisation of
strings and numbers. Both SDKs follow the sentence; they do not follow each
other.

# 3. The proposed change

`content_hash` is the first 16 lowercase hexadecimal characters of the SHA-256
digest of the **UTF-8 encoding of the RFC 8785 (JCS) serialisation** of the
`data` object, with absent optional fields omitted (as the specification already
requires of producers).

RFC 8785 fixes all three things the current sentence leaves open:

- **object members** sorted by their names as UTF-16 code units;
- **strings** written as UTF-8, escaping only `"`, `\` and control characters,
  with the short forms where they exist;
- **numbers** written with the ECMAScript `Number.prototype.toString` algorithm
  (so `1e-7`, `0.000015`, `2.5e+21`, and `25600` for a whole value).

A value that RFC 8785 cannot serialise (a NaN, an infinity, an integer beyond
the double-precision range) cannot be hashed; the producer omits `content_hash`
rather than invent a form for it, as the specification already allows (it is
optional).

# 4. Why RFC 8785 rather than a rule of our own

- It exists, is published by the IETF, and has implementations in many
  languages. An integrator in Go, Java or C# can use one instead of reading our
  SDK's source.
- It is close to what JavaScript does for strings and numbers, so the
  TypeScript change is small: write the members in order instead of building an
  object. An earlier draft of this memo said the TypeScript SDK was already
  conforming; integer-like keys show it is not (§1).
- A rule of our own ("escape everything", say) would have to define number
  formatting too, which is the harder half, and would still differ from every
  JCS library a third party might pick.

# 5. Compatibility level of this change

The change is to a producer obligation (how a SHOULD-field is computed). §4.1
and §4.2 do not classify it, so `GOVERNANCE.md` §4.4 does.

- **T1 (meaning).** Meaning is changed only where the previous version stated
  one (§4.4). IAES 2.0 stated "canonical JSON, sorted keys" and nothing about
  string escaping, number formatting or encoding. For the payloads where the
  SDKs disagree, 2.0 was **silent**, and this memo supplies the rule; supplying
  is not changing. For the payloads where they agree (ASCII strings, ordinary
  numbers -- §1), JCS gives the same bytes, so nothing a 2.0 producer emitted
  there changes. T1 does not answer MAJOR.
- **T2 (cross-version).** A consumer declaring 2.1 receives a 2.0 event with a
  `content_hash` computed by the Python SDK over Spanish text. If the consumer
  compares received hashes, nothing changes. If it **recomputes** the hash and
  compares, it gets a different value. The event is still consumable with the
  meaning 2.0 gave it. So T2 answers **MINOR**, provided only implementations
  that declare 2.1 must adopt JCS.

**What can go wrong, stated plainly.** Consumers deduplicate on `content_hash` +
`asset.asset_id` + `event_type`, and fall back to `event_id` **only when
`content_hash` is absent** (`IAES_SPEC.md`, *Consumers*, item 2). An earlier
draft of this memo said `event_id` "still identifies the event"; under that rule
it does not, when a hash is present. So the failure mode is this. A producer
emits an event, the send fails, the SDK is upgraded, and the retry recomputes
`content_hash` with JCS. The consumer receives two hashes for one event and
processes it twice: a missed duplicate, never a false merge.

The SDKs close that case themselves: **the hash is computed by the rule of the
`spec_version` the event declares.** An event built as 2.0 and retried after
the upgrade still declares 2.0, so it keeps its 2.0 hash; only events built as
2.1 use JCS. What remains is a consumer that recomputes hashes for events from
mixed versions. That is a broken expectation, not a broken guarantee
(`GOVERNANCE.md` §8 item 2), and the release notes disclose it.

# 6. Effect on existing implementers

Every implementation changes; none is JCS today (§1).

- **Python SDK** (`src/iaes/envelope.py`): `compute_content_hash` serialises with
  JCS for events that declare 2.1 or later. The SDK has no runtime dependencies,
  so this is done in-house:
  - keys sorted by **UTF-16 code unit** (`sorted(keys, key=lambda k:
    k.encode("utf-16-be"))`), not by code point, which is what `sort_keys=True`
    does;
  - strings unescaped (`ensure_ascii=False`) except `"`, `\` and control
    characters;
  - UTF-8 bytes;
  - a number formatter that follows the ECMAScript algorithm. Python's `repr`
    already gives the shortest round-trip digits; only the exponent form differs
    (JavaScript uses one only below 1e-6 or from 1e21 up, and writes `e-7`,
    not `e-07`).

  `_normalize_for_hash` is replaced by the formatter. Events that declare 2.0
  keep the 2.0 computation (§5).
- **TypeScript SDK** (`npm/src/envelope.ts`): write members in sorted order while
  serialising, instead of building a sorted object and calling
  `JSON.stringify`. Same version rule.
- **Node-RED and n8n**: use the TypeScript SDK; they change with it.
- **Ignition reference scenario**: its Jython script must follow the same rules
  (it is Python 2.7 there); the reference story's values are unaffected.
- **Consumers** that recompute `content_hash`: recompute by the rule of the
  event's `spec_version`, or compare received values.
- **Tests**: the shared conformance cases (wertek-ai/iaes#63, `content_hash.json`)
  record each implementation's 2.0 output for the six divergent payloads. This
  memo adds the JCS bytes for each and RFC 8785's own examples. Every
  implementation must produce them for 2.1 events and keep its recorded 2.0
  output for 2.0 events.

# 7. Worked example

`data` = `{"reason": "disparo de protección", "value": 0.000015, "unit": "mm/s"}`

JCS serialisation (UTF-8 bytes of this text, keys sorted):

```
{"reason":"disparo de protección","unit":"mm/s","value":0.000015}
```

`content_hash` = the first 16 hex characters of SHA-256 over those bytes:
**`a8fa4472a659449f`** -- what the TypeScript SDK at 2.0.2 already returns
(verified 2026-10-06 by hashing the bytes directly). The Python SDK at 2.0.2
hashes `{"reason":"disparo de protección","unit":"mm/s","value":1.5e-05}`
instead and returns `f9a88c450d8af801`.

# 8. Proposed incorporation

When Accepted, in the same change:

- `IAES_SPEC.md`, *Producers* item 6 and the envelope table's `content_hash`
  row: the rule of §3, citing RFC 8785; the version history row.
- `references/registry.json`: RFC 8785 (IETF, 2020).
- Both SDKs and the Ignition scenario (non-normative implementations), with the
  cross-language tests of §6.

# 9. What this memo does not decide

- Whether `content_hash` should cover more than `data` (the envelope, the asset).
- Whether consumers should recompute it at all.
- A longer prefix than 16 characters.

# 10. Open questions

1. **Old hashes.** Answered in this revision by the version rule (§5): the hash
   follows the `spec_version` the event declares, so a 2.0 event keeps its 2.0
   hash. Still open: whether the specification should also tell consumers that
   2.0 hashes are implementation-dependent for the payloads in §1. Recommended:
   yes, in the 2.1 version-history row.
2. **Integers beyond 2^53.** IAES numbers are JSON numbers; should the
   specification say that values must stay within the double-precision range,
   so that every producer can hash them?

# Author

Gilberto Garza, Wertek AI -- steward of IAES.
