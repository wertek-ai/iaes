import type {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
} from 'n8n-workflow';

import { validate, ValidationError, findNonconformities } from '@iaes/sdk';

// This node keeps no rules of its own. It used to: a list of required envelope
// fields, a regex for event_type, a length check for content_hash and, in
// strict mode, a switch of required data fields per type -- a fourth copy of
// the standard. Measured on 2026-10-06 the switch had no case for
// asset.hierarchy, left out three fields the schemas require, and accepted
// null where every other validator rejects it.
//
// Now there are two verdicts, the same two the specification separates
// (IAES_SPEC.md, "An event can be schema-valid and non-conforming"):
//
//   - schema: the SDK's validate(), against the published schemas;
//   - conformance: the SDK's findNonconformities(), which checks the fields
//     the schemas annotate with a format (uuid, date-time, date, uri).
//
// The Python SDK, the TypeScript SDK and the Node-RED nodes give the same two
// answers for the same event; conformance/ in the repository is where that is
// measured.
//
// Strict mode routes a nonconforming event to the Invalid output; off, it goes
// to Valid with the fields named in iaes_validation.nonconformities. Before,
// strict mode meant "check the data fields": the schema now always does that,
// so an event with a missing required data field is Invalid in both modes.

interface ValidationResult {
	valid: boolean;
	errors: string[];
	nonconformities: string[];
	spec_version: string;
	event_type: string | null;
}

function describe(field: string): string {
	return `${field} does not conform to the specification`;
}

function validateIaesEvent(payload: Record<string, unknown>, strict: boolean): ValidationResult {
	const specVersion = typeof payload.spec_version === 'string' ? payload.spec_version : 'unknown';
	const eventType = typeof payload.event_type === 'string' ? payload.event_type : null;

	try {
		validate(payload);
	} catch (err) {
		// Anything but a ValidationError is a failure of the validator itself
		// (for example, ajv missing), not a verdict on the event.
		if (!(err instanceof ValidationError)) throw err;
		// Every problem in one pass: in strict mode the nonconforming fields are
		// reported alongside what the schema rejected.
		const nonconformities = findNonconformities(payload);
		return {
			valid: false,
			errors: (err.errors.length ? err.errors : [err.message]).concat(
				strict ? nonconformities.map(describe) : [],
			),
			nonconformities,
			spec_version: specVersion,
			event_type: eventType,
		};
	}

	const nonconformities = findNonconformities(payload);
	const errors = strict ? nonconformities.map(describe) : [];
	return {
		valid: errors.length === 0,
		errors,
		nonconformities,
		spec_version: specVersion,
		event_type: eventType,
	};
}

export class IaesValidate implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'IAES Validate',
		name: 'iaesValidate',
		icon: 'file:iaes.svg',
		group: ['transform'],
		version: 1,
		subtitle: 'Validate IAES v{{$parameter["specVersion"] || "2.0"}} event',
		description: 'Validate an IAES event envelope against the spec',
		defaults: { name: 'IAES Validate' },
		inputs: ['main'],
		outputs: ['main', 'main'],
		outputNames: ['Valid', 'Invalid'],
		properties: [
			{
				displayName: 'Input Field',
				name: 'inputField',
				type: 'string',
				default: 'payload',
				description: 'Field containing the IAES event JSON (use "payload" for msg.payload or empty for root)',
			},
			{
				displayName: 'Strict Mode',
				name: 'strictMode',
				type: 'boolean',
				default: false,
				description: 'When enabled, also rejects events that pass the schema but break the specification (identifiers that are not UUIDs, timestamps that are not RFC 3339 UTC, a dataschema that is not a URI)',
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const validItems: INodeExecutionData[] = [];
		const invalidItems: INodeExecutionData[] = [];

		for (let i = 0; i < items.length; i++) {
			const inputField = this.getNodeParameter('inputField', i) as string;
			const strictMode = this.getNodeParameter('strictMode', i) as boolean;

			let payload: Record<string, unknown>;
			if (inputField && inputField !== '') {
				payload = items[i].json[inputField] as Record<string, unknown>;
			} else {
				payload = items[i].json;
			}

			if (!payload || typeof payload !== 'object') {
				invalidItems.push({
					json: {
						...items[i].json,
						iaes_validation: {
							valid: false,
							errors: [`Field "${inputField}" is not an object or is missing`],
							nonconformities: [],
							spec_version: 'unknown',
							event_type: null,
						},
					},
				});
				continue;
			}

			const result = validateIaesEvent(payload, strictMode);

			const output = {
				json: {
					...items[i].json,
					iaes_validation: result,
				},
			};

			if (result.valid) {
				validItems.push(output);
			} else {
				invalidItems.push(output);
			}
		}

		return [validItems, invalidItems];
	}
}
