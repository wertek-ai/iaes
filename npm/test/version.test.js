/**
 * A version literal duplicated in two files always drifts.
 *
 * It already happened on the Python side: pyproject and PyPI published 0.3.0
 * while the package reported 0.2.1 at runtime, and the pinned test protected
 * the drift instead of catching it. The same shape exists here — SDK_VERSION
 * in client.ts against the version in package.json — and today they agree only
 * because nobody has bumped one without the other yet. This makes that fail
 * the build rather than ship a wrong User-Agent.
 */

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");

describe("version", () => {
  it("the User-Agent version matches the published package version", () => {
    const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
    const client = fs.readFileSync(path.join(root, "src", "client.ts"), "utf8");
    const match = client.match(/const SDK_VERSION\s*=\s*"([^"]+)"/);

    assert.ok(match, "SDK_VERSION not found in client.ts");
    assert.equal(
      match[1],
      pkg.version,
      `client.ts reports ${match[1]} but package.json publishes ${pkg.version}; ` +
        "the User-Agent would lie about which SDK made the request",
    );
  });

  it("the SDK targets the spec version it implements", () => {
    const { SPEC_VERSION } = require("../dist/index.js");
    const spec = fs.readFileSync(path.join(root, "..", "IAES_SPEC.md"), "utf8");
    const rows = [...spec.matchAll(/^\| (\d+\.\d+) \| /gm)].map((m) => m[1]);

    assert.ok(rows.length > 0, "no version history found in IAES_SPEC.md");
    assert.ok(
      rows.includes(SPEC_VERSION),
      `SPEC_VERSION ${SPEC_VERSION} is not in the specification's version history (${rows.join(", ")})`,
    );
  });
});
