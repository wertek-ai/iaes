/**
 * The n8n package shipped for a whole major with no tests at all, and it cost
 * two defects that a single decoy would have caught:
 *
 *   - the validate node hardcoded the specification's major, so a package
 *     published as 2.0.0 rejected every 2.0 event the SDK beside it produces;
 *   - it rejected any event_type outside the published seven, closing a catalog
 *     the specification opens and telling consumers they MUST NOT close.
 *
 * Both were found by review, not by the suite, because there was no suite.
 * This is the suite.
 *
 * It runs against `dist/`, which is what the package publishes — checking the
 * source would pass over a build that never emitted the fix.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const { IaesValidate } = require(path.join(__dirname, '..', 'dist', 'nodes', 'IaesValidate', 'IaesValidate.node.js'));
const { SPEC_VERSION } = require('@iaes/sdk');

/** Drive the node the way n8n does, with one item in and two outputs out. */
async function validate(payload, { strict = false } = {}) {
  const node = new IaesValidate();
  const context = {
    getInputData: () => [{ json: { payload } }],
    getNodeParameter: (name) => (name === 'inputField' ? 'payload' : strict),
  };
  const [valid, invalid] = await node.execute.call(context);
  return {
    valid: valid.length === 1,
    errors: (invalid[0] || valid[0] || {}).json.iaes_validation.errors,
  };
}

const base = {
  spec_version: SPEC_VERSION,
  event_id: '550e8400-e29b-41d4-a716-446655440000',
  correlation_id: '550e8400-e29b-41d4-a716-446655440000',
  timestamp: '2026-09-08T12:00:00Z',
  source: 'acme.press',
  asset: { asset_id: 'PRESS-01' },
};

test('a published event type validates', async () => {
  const r = await validate({
    ...base,
    event_type: 'asset.health',
    data: { health_index: 0.8, severity: 'medium' },
  });
  assert.ok(r.valid, `rejected: ${JSON.stringify(r.errors)}`);
});

test('a custom event_type is wire-valid and MUST NOT error', async () => {
  // The specification lets a producer emit its own type in a namespace it
  // controls, and omit dataschema. An unknown type is not an invalid event.
  const r = await validate({
    ...base,
    event_type: 'acme.press_stroke',
    data: { stroke: 42 },
  });
  assert.ok(r.valid, `a custom event_type was rejected: ${JSON.stringify(r.errors)}`);
});

test('an event_type that is not dot-notation is still invalid', async () => {
  // The door opens for a namespaced type, not for anything at all.
  const r = await validate({ ...base, event_type: 'NotDotNotation', data: {} });
  assert.ok(!r.valid, 'a malformed event_type must still be rejected');
});

test('the accepted spec_version follows the SDK, not a hardcoded major', async () => {
  // This is the one that shipped: a 2.0.0 package rejecting 2.0 events.
  const r = await validate({
    ...base,
    event_type: 'asset.health',
    data: { health_index: 0.8, severity: 'medium' },
  });
  assert.ok(r.valid, `the node rejects the SDK's own SPEC_VERSION ${SPEC_VERSION}`);

  const wrongMajor = `${Number(SPEC_VERSION.split('.')[0]) + 1}.0`;
  const other = await validate({
    ...base,
    spec_version: wrongMajor,
    event_type: 'asset.health',
    data: { health_index: 0.8, severity: 'medium' },
  });
  assert.ok(!other.valid, `${wrongMajor} should not validate against a ${SPEC_VERSION} node`);
});
