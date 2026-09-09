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

// ---------------------------------------------------------------------------
// A valid value is not a sentinel. The schemas give several optional numerics
// `minimum: 0`, so 0 is an answer -- RUL zero, due now, zero seconds -- and the
// form used to collapse it to "not given" with `|| undefined`. This is a
// census: every optional numeric with minimum 0 in the six schemas is either
// mapped to a form parameter here, where 0 must survive to the wire, or
// declared NOT exposed. A new numeric on the form that is in neither list
// fails the census.

const EXPOSED = {
  // schema field -> [event type, form parameter, the params that make the event valid]
  rul_days: ['asset.health', 'rulDays', { healthIndex: 0.5, severity: 'high' }],
  recommended_due_days: ['maintenance.work_order_intent', 'recommendedDueDays', { woTitle: 'Inspect', woPriority: 'high' }],
  actual_duration_seconds: ['maintenance.completion', 'durationSeconds', { workOrderId: 'WO-1', completionStatus: 'completed' }],
};
const NOT_EXPOSED = [
  'sampling_rate_hz', 'acquisition_duration_s', 'estimated_downtime_hours',
  'checklist_completion_pct', 'spare_parts_count', 'unit_cost', 'total_cost',
  // Not on the form at all. They WERE given a default by the SDK itself, in
  // both languages, against the specification's own example; fixed in 2.0.2
  // (npm/test/absent-scores.test.js and tests/test_models.py keep it fixed).
  'anomaly_score', 'fault_confidence',
];

test('the census of optional numerics that allow zero is complete', () => {
  const census = new Set();
  for (const file of fs.readdirSync(SCHEMAS).filter((f) => f.endsWith('.schema.json') && !f.startsWith('iaes-envelope') && !f.startsWith('asset-hierarchy'))) {
    const data = JSON.parse(fs.readFileSync(path.join(SCHEMAS, file), 'utf-8')).properties.data;
    const required = new Set(data.required || []);
    for (const [name, def] of Object.entries(data.properties)) {
      const types = [].concat(def.type);
      if (!required.has(name) && def.minimum === 0 && (types.includes('number') || types.includes('integer'))) census.add(name);
    }
  }
  assert.deepEqual([...census].sort(), [...Object.keys(EXPOSED), ...NOT_EXPOSED].sort(),
    'a numeric optional that allows zero is neither mapped to the form nor declared unexposed');
  // And the "not exposed" list must be true: none of those is a form parameter's field.
  const params = new Set(new IaesEmit().description.properties.map((p) => p.name));
  for (const [, [, param]] of Object.entries(EXPOSED)) assert.ok(params.has(param), `${param} is not a form parameter`);
});

for (const [field, [eventType, param, valid]] of Object.entries(EXPOSED)) {
  test(`${field}: zero survives to the wire, unspecified is omitted`, async () => {
    const base = { eventType, assetId: 'A-1', source: 'test', outputMode: 'envelope', ...valid };
    assert.equal((await emit({ ...base, [param]: 0 })).data[field], 0, '0 is a valid value and must be emitted');
    assert.equal((await emit({ ...base, [param]: 7 })).data[field], 7);
    assert.ok(!(field in (await emit(base)).data), 'the form default must mean "not specified"');
    assert.ok(!(field in (await emit({ ...base, [param]: -1 })).data), '-1 is the sentinel and must be omitted');
  });
}
