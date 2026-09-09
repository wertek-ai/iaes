/**
 * The emit node, driven the way n8n drives it, from `dist/`.
 *
 * The first defect here was found by the reference scenarios, not by a suite:
 * a 4.2 mm/s RMS reading could not say "rms" from this node, because the form
 * had no field for `units_qualifier`. The same story told in Python,
 * TypeScript and Node-RED carried the qualifier and n8n silently did not --
 * a consumer comparing the four would have seen one measurement that could be
 * peak, peak-to-peak or RMS, and no way to tell.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const { IaesEmit } = require(path.join(__dirname, '..', 'dist', 'nodes', 'IaesEmit', 'IaesEmit.node.js'));

/** Drive the node with one empty item and the given parameters; defaults fill the rest. */
async function emit(params) {
  const node = new IaesEmit();
  const defaults = new Map(node.description.properties.map((p) => [p.name, p.default]));
  const context = {
    getInputData: () => [{ json: {} }],
    getNodeParameter: (name) => (name in params ? params[name] : defaults.get(name)),
  };
  const [items] = await node.execute.call(context);
  return items[0].json;
}

const measurement = {
  eventType: 'asset.measurement',
  assetId: 'MOTOR-001',
  source: 'sensor.line1',
  measurementType: 'vibration_velocity',
  value: 4.2,
  unit: 'mm/s',
  outputMode: 'envelope',
};

test('a measurement can say how its value was derived', async () => {
  const event = await emit({ ...measurement, unitsQualifier: 'rms' });
  assert.equal(event.data.units_qualifier, 'rms');
});

test('an empty qualifier is omitted, not sent as ""', async () => {
  // The schema types the field as string or null; an empty string would be a
  // qualifier that says nothing while claiming to say something.
  const event = await emit({ ...measurement, unitsQualifier: '' });
  assert.ok(!('units_qualifier' in event.data), `got ${JSON.stringify(event.data)}`);
});

test('the chain parameters reach the envelope', async () => {
  const chain = '3f2504e0-4f89-11d3-9a0c-0305e82c3303';
  const parent = '9b2e7c1a-2f4e-4c3b-8d1e-5a6f7b8c9d0e';
  const event = await emit({ ...measurement, correlationId: chain, sourceEventId: parent });
  assert.equal(event.correlation_id, chain);
  assert.equal(event.source_event_id, parent);
});
