/**
 * The TypeScript SDK against the shared conformance cases (conformance/).
 *
 * The same cases run in the Python SDK, the Node-RED nodes and the n8n nodes;
 * agreement between them is what the suite exists to make measurable. See
 * conformance/README.md.
 */

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const {
  validate,
  ValidationError,
  findNonconformities,
  computeContentHash,
  canonicalJson,
} = require("../dist/index.js");

const DIR = path.join(__dirname, "..", "..", "conformance");
const CASES = JSON.parse(fs.readFileSync(path.join(DIR, "validation.json"), "utf-8")).cases;
const HASHES = JSON.parse(fs.readFileSync(path.join(DIR, "content_hash.json"), "utf-8")).cases;

test("the suite has each kind of case", () => {
  // Control: a suite with no rejected or no nonconforming case proves nothing.
  const kinds = new Set(CASES.map((c) => `${c.expect.schema_valid}/${c.expect.conforming}`));
  assert.deepEqual([...kinds].sort(), ["false/false", "true/false", "true/true"]);
});

for (const c of CASES) {
  test(`schema verdict: ${c.id}`, () => {
    let got;
    try {
      validate(c.event);
      got = true;
    } catch (e) {
      // Anything but ValidationError is a crash, not a verdict.
      if (!(e instanceof ValidationError)) throw e;
      got = false;
    }
    assert.equal(got, c.expect.schema_valid, c.title);
  });

  if (c.expect.schema_valid) {
    test(`nonconforming fields: ${c.id}`, () => {
      assert.deepEqual(findNonconformities(c.event), c.expect.nonconforming_fields, c.title);
    });
  }
}

test("the hash suite has each kind of case", () => {
  // Control: a suite with no refusal or no version switch proves nothing about either.
  const kinds = [...new Set(HASHES.map((c) => c.status))].sort();
  assert.deepEqual(kinds, ["agreed", "divergent_2_0", "jcs_only", "jcs_reject", "version_switch"]);
});

for (const c of HASHES) {
  if (c.status === "agreed" || c.status === "divergent_2_0") {
    // 2.0 events keep the 2.0 rule (IAES-RFC-011 §5): what this SDK produced before.
    test(`content_hash 2.0: ${c.id}`, () => {
      const expected =
        c.status === "agreed" ? c.content_hash : c.by_implementation.typescript.content_hash;
      assert.equal(computeContentHash(c.data, "2.0"), expected, c.title);
    });
  }
  if (c.status === "jcs_reject") {
    // A value RFC 8785 cannot serialise is refused, never hashed some other way.
    test(`content_hash 2.1 (JCS) refuses: ${c.id}`, () => {
      assert.throws(() => canonicalJson(c.data), Error, c.title);
      assert.throws(() => computeContentHash(c.data, "2.1"), Error, c.title);
    });
    continue;
  }
  if (c.status === "version_switch") {
    // JCS only for 2.<minor> with minor >= 1; absent or unreadable keeps the 2.0
    // rule. An absent spec_version is passed explicitly as undefined, which is
    // what event.spec_version gives.
    test(`content_hash rule by declared version: ${c.id}`, () => {
      const expected =
        c.rule === "jcs" ? c.jcs.content_hash : c.by_implementation.typescript.content_hash;
      assert.equal(computeContentHash(c.data, c.spec_version), expected, c.title);
    });
  }
  // 2.1 and later hash RFC 8785 (JCS): the same bytes in every implementation.
  test(`content_hash 2.1 (JCS): ${c.id}`, () => {
    assert.equal(canonicalJson(c.data), c.jcs.canonical, c.title);
    assert.equal(computeContentHash(c.data, "2.1"), c.jcs.content_hash, c.title);
  });
}
