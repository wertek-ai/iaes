/**
 * canonicalJson beyond the shared vectors: values JSON cannot carry, which a
 * JSON file therefore cannot hold, so conformance/content_hash.json cannot
 * test them. JSON.stringify writes a Date as a string, and a Map, a Set or a
 * class instance as "{}", so two different values would hash the same.
 */

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");

const { canonicalJson, computeContentHash, AssetMeasurement } = require("../dist/index");

class Reading {
  constructor() {
    this.value = 1;
  }
}

describe("canonicalJson refuses what is not a JSON value", () => {
  for (const [name, value] of [
    ["Date", new Date(0)],
    ["Map", new Map([["a", 1]])],
    ["Set", new Set([1])],
    ["a class instance", new Reading()],
  ]) {
    it(`refuses a ${name}`, () => {
      assert.throws(() => canonicalJson({ v: value }), /not a JSON object/);
      assert.throws(() => computeContentHash({ v: value }, "2.1"), /not a JSON object/);
    });
  }

  it("accepts an object with no prototype: it is still a plain object", () => {
    const bare = Object.create(null);
    bare.b = 2;
    bare.a = 1;
    assert.equal(canonicalJson({ v: bare }), '{"v":{"a":1,"b":2}}');
  });

  it("2.0 events keep the 2.0 rule, unchanged", () => {
    // The 2.0 computation is JSON.stringify over sorted keys, and it is frozen:
    // a Date there is still written as its ISO string.
    assert.equal(computeContentHash({ v: new Date(0) }, "2.0").length, 16);
  });
});

describe("lone surrogates on a Node without String.prototype.isWellFormed", () => {
  // engines allows Node >= 16; isWellFormed arrived in Node 20. The fallback is
  // a regular expression, and it must answer as the native method does.
  it("refuses them, and accepts a proper pair", () => {
    const native = String.prototype.isWellFormed;
    delete String.prototype.isWellFormed;
    try {
      assert.equal("isWellFormed" in String.prototype, false, "control: the fallback is what runs");
      for (const bad of ["a\ud800b", "\udc00", "x\udc00", "\ud83d", "😀\udc00"]) {
        assert.throws(() => canonicalJson({ s: bad }), /lone surrogate/, JSON.stringify(bad));
        assert.throws(() => canonicalJson({ [bad]: 1 }), /lone surrogate/, JSON.stringify(bad));
      }
      assert.equal(canonicalJson({ s: "😀" }), '{"s":"😀"}');
    } finally {
      if (native) String.prototype.isWellFormed = native;
    }
  });
});

describe("integers RFC 8785 can carry are hashed, not refused", () => {
  it("a measurement of 1e16 builds and hashes as 10000000000000000", () => {
    const event = new AssetMeasurement({
      asset_id: "A", measurement_type: "counter", value: 1e16, unit: "count",
      timestamp: "2026-10-07T00:00:00Z",
    }).toJSON();
    assert.equal(event.content_hash, computeContentHash({ measurement_type: "counter", unit: "count", value: 1e16 }));
    assert.equal(canonicalJson({ value: 1e16 }), '{"value":10000000000000000}');
  });
});
