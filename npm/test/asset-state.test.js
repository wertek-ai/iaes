/**
 * asset.state (IAES 2.1, IAES-RFC-010) in the TypeScript SDK.
 *
 * The properties that make the type different from the other seven: it never
 * carries content_hash, its timestamp is the instant of the transition, and
 * it round-trips through fromObject without one.
 */

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");

const {
  AssetState,
  UpDownState,
  DownKind,
  DownCause,
  UpMode,
  PreviousState,
  fromObject,
  validate,
  ValidationError,
} = require("../dist/index");

const TRIP = {
  asset_id: "PUMP-101",
  source: "plant.scada",
  timestamp: "2026-10-06T06:10:00Z",
  state: UpDownState.DOWN,
  down_kind: DownKind.UNPLANNED,
  down_cause: DownCause.OTHER_UNPLANNED,
  previous_state: PreviousState.UP,
  detail: "trip",
};

describe("asset.state", () => {
  it("never carries content_hash, and validates", () => {
    const event = new AssetState(TRIP).toJSON();
    assert.equal("content_hash" in event, false);
    assert.equal(event.spec_version, "2.1");
    assert.equal(event.dataschema, "https://iaes.dev/schema/v2/asset.state");
    validate(event);
  });

  it("keeps the timestamp it was given: the instant of the transition", () => {
    assert.equal(new AssetState(TRIP).toJSON().timestamp, "2026-10-06T06:10:00Z");
  });

  it("two identical trips are two events, told apart only by event_id", () => {
    const a = new AssetState(TRIP).toJSON();
    const b = new AssetState(TRIP).toJSON();
    assert.deepEqual(a.data, b.data);
    assert.notEqual(a.event_id, b.event_id);
  });

  it("round-trips through fromObject", () => {
    const event = new AssetState({ ...TRIP, state: UpDownState.UP, up_mode: UpMode.RUNNING,
      down_kind: undefined, down_cause: undefined }).toJSON();
    const back = fromObject(event);
    assert.ok(back instanceof AssetState);
    assert.deepEqual(back.toJSON().data, event.data);
  });

  it("the schema rejects a content_hash, naming the field", () => {
    const event = { ...new AssetState(TRIP).toJSON(), content_hash: "0123456789abcdef" };
    assert.throws(() => validate(event), (err) =>
      err instanceof ValidationError && /content_hash/.test(err.message));
  });

  it("an unpublished down_cause is not classified, not invalid", () => {
    validate(new AssetState({ ...TRIP, down_kind: "planned", down_cause: "acme_shift_change" }).toJSON());
  });

  it("requires timestamp: for this type it is the fact, not the time of sending", () => {
    const { timestamp, ...withoutTimestamp } = TRIP;
    assert.throws(() => new AssetState(withoutTimestamp), /requires timestamp/);
  });

  it("the schema rejects fields of the other state", () => {
    // up with a down kind or a down cause, down with an up mode.
    const up = { ...TRIP, state: UpDownState.UP, down_kind: undefined, down_cause: undefined };
    for (const extra of [{ down_kind: "planned" }, { down_cause: "acme_shift_change" }]) {
      assert.throws(() => validate(new AssetState({ ...up, ...extra }).toJSON()), ValidationError);
    }
    assert.throws(() => validate(new AssetState({ ...TRIP, up_mode: UpMode.RUNNING }).toJSON()),
      ValidationError);
    // Control: the same up event without them is valid.
    validate(new AssetState({ ...up, up_mode: UpMode.RUNNING }).toJSON());
  });

  it("the schema rejects asset.state declared as 2.0, where the type does not exist", () => {
    const event = { ...new AssetState(TRIP).toJSON(), spec_version: "2.0" };
    assert.throws(() => validate(event), ValidationError);
  });

  it("never computes a hash, so text RFC 8785 cannot serialise does not fail it", () => {
    const event = new AssetState({ ...TRIP, reason: "a\ud800b" }).toJSON();
    assert.equal("content_hash" in event, false);
  });
});
