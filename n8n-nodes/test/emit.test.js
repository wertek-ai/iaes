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

// ---------------------------------------------------------------------------
// The class, not three fields. IAES_SPEC.md: "A producer MUST omit an optional
// field it was not given rather than substitute a value for it." A form is a
// producer, and a form default with a meaning is that substitution. This test
// drives the node with ONLY the schema's required fields and compares what it
// emits with what the SDK itself emits for the same required fields. Whatever
// the SDK adds is the SDK's business (and identical in every implementation);
// whatever the FORM adds on top is a default asserting something nobody said.
// It found failure_confirmed: false, triggered_by: "threshold" and
// recommended_due_days: 7, and it will find the next one.

const sdk = require('@iaes/sdk');
const fs = require('node:fs');

const SCHEMAS = path.join(path.dirname(require.resolve('@iaes/sdk/package.json')), 'schemas');

// Per event type: the SDK class, and the form parameter that carries each
// required schema field, with a valid value for it.
const REQUIRED = {
  'asset.measurement': { Model: sdk.AssetMeasurement, fields: { measurement_type: ['measurementType', 'vibration_velocity'], value: ['value', 4.2], unit: ['unit', 'mm/s'] } },
  'asset.health': { Model: sdk.AssetHealth, fields: { health_index: ['healthIndex', 0.58], severity: ['severity', 'high'] } },
  'maintenance.work_order_intent': { Model: sdk.WorkOrderIntent, fields: { title: ['woTitle', 'Inspect'], priority: ['woPriority', 'high'] } },
  'maintenance.completion': { Model: sdk.MaintenanceCompletion, fields: { work_order_id: ['workOrderId', 'WO-1'], status: ['completionStatus', 'completed'] } },
  'sensor.registration': { Model: sdk.SensorRegistration, fields: { sensor_id: ['regSensorId', 'S-1'], registration_status: ['registrationStatus', 'registered'] } },
  'maintenance.spare_part_usage': { Model: sdk.SparePartUsage, fields: { work_order_id: ['spareWoId', 'WO-1'], spare_part_id: ['sparePartId', 'P-1'], quantity_used: ['quantityUsed', 1] } },
};

for (const [eventType, { Model, fields }] of Object.entries(REQUIRED)) {
  test(`${eventType}: the form adds nothing the SDK would not (only required fields given)`, async () => {
    // The mapping above must cover exactly the schema's required list, or
    // this test would be quietly checking the wrong fields.
    const schema = JSON.parse(fs.readFileSync(path.join(SCHEMAS, `${eventType.replace('.', '-').replace(/_/g, '-')}.schema.json`), 'utf-8'));
    assert.deepEqual(Object.keys(fields).sort(), [...schema.properties.data.required].sort(),
      `${eventType}: this test's required-field map is out of step with the schema`);

    const params = { eventType, assetId: 'A-1', source: 'test', outputMode: 'envelope' };
    const sdkInit = { asset_id: 'A-1', source: 'test' };
    for (const [field, [param, value]] of Object.entries(fields)) { params[param] = value; sdkInit[field] = value; }

    const fromForm = await emit(params);
    const fromSdk = new Model(sdkInit).toJSON();
    const extra = Object.keys(fromForm.data).filter((k) => !(k in fromSdk.data));
    assert.deepEqual(extra, [],
      `${eventType}: the form asserted ${JSON.stringify(extra)} without being told to (${JSON.stringify(fromForm.data)})`);
    assert.deepEqual(fromForm.data, fromSdk.data);
  });
}

test('failure_confirmed is three-state, and an explicit "false" is still an assertion', async () => {
  const base = { eventType: 'maintenance.completion', assetId: 'A-1', source: 'test', workOrderId: 'WO-1', completionStatus: 'completed', outputMode: 'envelope' };
  assert.ok(!('failure_confirmed' in (await emit(base)).data), 'unspecified must be omitted');
  assert.equal((await emit({ ...base, failureConfirmed: 'false' })).data.failure_confirmed, false);
  assert.equal((await emit({ ...base, failureConfirmed: 'true' })).data.failure_confirmed, true);
  // Workflows saved before 2.0.2 carry a boolean. It was an explicit choice.
  assert.equal((await emit({ ...base, failureConfirmed: false })).data.failure_confirmed, false);
});
