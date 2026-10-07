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

for (const c of HASHES) {
  if (c.status !== "jcs_only") {
    // 2.0 events keep the 2.0 rule (IAES-RFC-011 §5): what this SDK produced before.
    test(`content_hash 2.0: ${c.id}`, () => {
      const expected =
        c.status === "agreed" ? c.content_hash : c.by_implementation.typescript.content_hash;
      assert.equal(computeContentHash(c.data, "2.0"), expected, c.title);
    });
  }
  // 2.1 and later hash RFC 8785 (JCS): the same bytes in every implementation.
  test(`content_hash 2.1 (JCS): ${c.id}`, () => {
    assert.equal(canonicalJson(c.data), c.jcs.canonical, c.title);
    assert.equal(computeContentHash(c.data, "2.1"), c.jcs.content_hash, c.title);
  });
}
