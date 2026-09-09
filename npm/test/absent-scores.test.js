/**
 * An absent optional score is not an assertion.
 *
 * IAES_SPEC.md, Producers 3: a producer MUST omit an optional field it was
 * not given rather than substitute a value for it, and its own example is
 * `anomaly_score: 0.0`. This SDK wrote exactly that for every asset.health
 * whose producer said nothing -- RFC-002 §6 calls it the real defect -- and
 * no test noticed, because none asked what the wire looked like when a field
 * was NOT given. These do. Against dist/, which is what the package publishes.
 */

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { AssetHealth } = require("../dist/index");

const base = { asset_id: "M-1", health_index: 0.42, severity: "high", source: "test" };

describe("asset.health optional scores", () => {
  it("are omitted from the wire when the producer did not supply them", () => {
    const { data } = new AssetHealth(base).toJSON();
    assert.ok(!("anomaly_score" in data), "anomaly_score was substituted: " + JSON.stringify(data));
    assert.ok(!("fault_confidence" in data), "fault_confidence was substituted: " + JSON.stringify(data));
  });

  it("a supplied zero is a score and stays on the wire", () => {
    const { data } = new AssetHealth({ ...base, anomaly_score: 0, fault_confidence: 0 }).toJSON();
    assert.equal(data.anomaly_score, 0);
    assert.equal(data.fault_confidence, 0);
  });

  it("a supplied value stays on the wire", () => {
    const { data } = new AssetHealth({ ...base, anomaly_score: 0.92, fault_confidence: 0.87 }).toJSON();
    assert.equal(data.anomaly_score, 0.92);
    assert.equal(data.fault_confidence, 0.87);
  });

  it("each score is independent", () => {
    const { data } = new AssetHealth({ ...base, anomaly_score: 0.5 }).toJSON();
    assert.equal(data.anomaly_score, 0.5);
    assert.ok(!("fault_confidence" in data));
  });

  it("a round trip keeps an absent score absent, and a present one present", () => {
    const absent = AssetHealth.fromObject(new AssetHealth(base).toJSON()).toJSON().data;
    assert.ok(!("anomaly_score" in absent) && !("fault_confidence" in absent));
    const present = AssetHealth.fromObject(new AssetHealth({ ...base, anomaly_score: 0.3 }).toJSON()).toJSON().data;
    assert.equal(present.anomaly_score, 0.3);
  });

  it("the public API is unchanged: the properties still read as numbers, 0 when not given", () => {
    // 2.0.1 broke source compatibility in a patch once; the review caught it.
    // The fix lives beside the instance, not on its type.
    const e = new AssetHealth(base);
    assert.equal(typeof e.anomaly_score, "number");
    assert.equal(e.anomaly_score, 0);
    assert.equal(e.fault_confidence, 0);
    assert.deepEqual(Object.keys(e).filter((k) => /supplied/i.test(k)), [], "no new property leaked onto the instance");
  });
});
