/**
 * The n8n IAES Validate node against the shared conformance cases
 * (conformance/), in both modes. The same cases run in the Python SDK, the
 * TypeScript SDK and the Node-RED nodes; see conformance/README.md.
 *
 * Runs against dist/, which is what n8n loads.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { IaesValidate } = require(path.join(__dirname, '..', 'dist', 'nodes', 'IaesValidate', 'IaesValidate.node.js'));

const DIR = path.join(__dirname, '..', '..', 'conformance');
const CASES = JSON.parse(fs.readFileSync(path.join(DIR, 'validation.json'), 'utf-8')).cases;

/** Drive the node the way n8n does: one item in, two outputs out. */
async function run(event, strict) {
	const node = new IaesValidate();
	const context = {
		getInputData: () => [{ json: { payload: event } }],
		getNodeParameter: (name) => (name === 'inputField' ? 'payload' : strict),
	};
	const [valid, invalid] = await node.execute.call(context);
	const item = (valid[0] || invalid[0]).json.iaes_validation;
	return { valid: valid.length === 1, result: item };
}

for (const c of CASES) {
	test(`default mode: ${c.id}`, async () => {
		const r = await run(c.event, false);
		assert.equal(r.valid, c.expect.schema_valid, c.title);
		if (c.expect.schema_valid) {
			assert.deepEqual(r.result.nonconformities, c.expect.nonconforming_fields, c.title);
		}
	});

	test(`strict mode: ${c.id}`, async () => {
		const r = await run(c.event, true);
		assert.equal(r.valid, c.expect.conforming, c.title);
	});
}
