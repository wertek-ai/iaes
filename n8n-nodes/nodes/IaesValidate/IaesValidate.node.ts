import type {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
} from 'n8n-workflow';

import { SPEC_VERSION } from '@iaes/sdk';

const VALID_EVENT_TYPES = [
	'asset.measurement',
	'asset.health',
	'maintenance.work_order_intent',
	'maintenance.completion',
	'asset.hierarchy',
	'sensor.registration',
	'maintenance.spare_part_usage',
];

const REQUIRED_ENVELOPE_FIELDS = [
	'spec_version',
	'event_type',
	'event_id',
	'correlation_id',
	'timestamp',
	'source',
	'asset',
	'data',
];

interface ValidationResult {
	valid: boolean;
	errors: string[];
	spec_version: string;
	event_type: string | null;
}

function validateIaesEvent(payload: Record<string, unknown>): ValidationResult {
	const errors: string[] = [];

	// Check required envelope fields
	for (const field of REQUIRED_ENVELOPE_FIELDS) {
		if (!(field in payload) || payload[field] === null || payload[field] === undefined) {
			errors.push(`Missing required field: ${field}`);
		}
	}

	// Validate spec_version
	const specVersion = payload.spec_version as string;
	if (specVersion && !/^1\.\d+$/.test(specVersion)) {
		errors.push(`Invalid spec_version "${specVersion}" — must match ^1.\\d+$`);
	}

	// Validate event_type
	const eventType = payload.event_type as string;
	if (eventType && !VALID_EVENT_TYPES.includes(eventType)) {
		errors.push(`Unknown event_type "${eventType}" — valid: ${VALID_EVENT_TYPES.join(', ')}`);
	}

	// Validate asset object
	const asset = payload.asset as Record<string, unknown> | undefined;
	if (asset) {
		if (!asset.asset_id) {
			errors.push('Missing required field: asset.asset_id');
		}
	}

	// Validate timestamp format
	const timestamp = payload.timestamp as string;
	if (timestamp) {
		const parsed = Date.parse(timestamp);
		if (isNaN(parsed)) {
			errors.push(`Invalid timestamp "${timestamp}" — must be ISO 8601`);
		}
	}

	// Validate content_hash format (if present)
	const contentHash = payload.content_hash as string;
	if (contentHash && (typeof contentHash !== 'string' || contentHash.length !== 16)) {
		errors.push(`Invalid content_hash — must be 16-char hex string`);
	}

	// Validate data is an object
	const data = payload.data;
	if (data !== undefined && (typeof data !== 'object' || data === null || Array.isArray(data))) {
		errors.push('Field "data" must be an object');
	}

	return {
		valid: errors.length === 0,
		errors,
		spec_version: specVersion || 'unknown',
		event_type: eventType || null,
	};
}

export class IaesValidate implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'IAES Validate',
		name: 'iaesValidate',
		icon: 'file:iaes.svg',
		group: ['transform'],
		version: 1,
		subtitle: 'Validate IAES v{{$parameter["specVersion"] || "1.3"}} event',
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
				description: 'When enabled, also validates event-type-specific required fields in data',
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
							spec_version: 'unknown',
							event_type: null,
						},
					},
				});
				continue;
			}

			const result = validateIaesEvent(payload);

			// Strict mode: check event-type-specific required fields
			if (strictMode && result.event_type) {
				const data = payload.data as Record<string, unknown>;
				if (data) {
					switch (result.event_type) {
						case 'asset.health':
							if (!('health_index' in data)) result.errors.push('data.health_index required');
							if (!('severity' in data)) result.errors.push('data.severity required');
							break;
						case 'asset.measurement':
							if (!('measurement_type' in data)) result.errors.push('data.measurement_type required');
							if (!('value' in data)) result.errors.push('data.value required');
							if (!('unit' in data)) result.errors.push('data.unit required');
							break;
						case 'maintenance.work_order_intent':
							if (!('title' in data)) result.errors.push('data.title required');
							break;
						case 'maintenance.completion':
							if (!('work_order_id' in data)) result.errors.push('data.work_order_id required');
							break;
						case 'sensor.registration':
							if (!('sensor_id' in data)) result.errors.push('data.sensor_id required');
							if (!('registration_status' in data)) result.errors.push('data.registration_status required');
							break;
						case 'maintenance.spare_part_usage':
							if (!('spare_part_id' in data)) result.errors.push('data.spare_part_id required');
							if (!('quantity_used' in data)) result.errors.push('data.quantity_used required');
							break;
					}
					result.valid = result.errors.length === 0;
				}
			}

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
