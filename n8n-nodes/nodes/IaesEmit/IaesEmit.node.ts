import type {
	IDataObject,
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
} from 'n8n-workflow';

import {
	AssetMeasurement,
	AssetHealth,
	WorkOrderIntent,
	MaintenanceCompletion,
	SensorRegistration,
	SparePartUsage,
} from '@iaes/sdk';

export class IaesEmit implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'IAES Emit',
		name: 'iaesEmit',
		icon: 'file:iaes.svg',
		group: ['transform'],
		version: 1,
		subtitle: '={{$parameter["eventType"]}}',
		description: 'Emit an IAES v1.3 industrial asset event',
		defaults: { name: 'IAES Emit' },
		inputs: ['main'],
		outputs: ['main'],
		credentials: [
			{
				name: 'iaesApi',
				required: false,
			},
		],
		properties: [
			// ── Event type selector ──
			{
				displayName: 'Event Type',
				name: 'eventType',
				type: 'options',
				noDataExpression: true,
				options: [
					{ name: 'Asset Health', value: 'asset.health' },
					{ name: 'Asset Measurement', value: 'asset.measurement' },
					{ name: 'Work Order Intent', value: 'maintenance.work_order_intent' },
					{ name: 'Maintenance Completion', value: 'maintenance.completion' },
					{ name: 'Sensor Registration', value: 'sensor.registration' },
					{ name: 'Spare Part Usage', value: 'maintenance.spare_part_usage' },
				],
				default: 'asset.health',
				description: 'IAES event type to emit',
			},

			// ── Common fields ──
			{
				displayName: 'Asset ID',
				name: 'assetId',
				type: 'string',
				default: '',
				required: true,
				placeholder: 'PUMP-001',
				description: 'Unique asset identifier',
			},
			{
				displayName: 'Source',
				name: 'source',
				type: 'string',
				default: 'n8n',
				description: 'Event source identifier',
			},
			{
				displayName: 'Asset Name',
				name: 'assetName',
				type: 'string',
				default: '',
				description: 'Human-readable asset name (optional)',
			},
			{
				displayName: 'Plant',
				name: 'plant',
				type: 'string',
				default: '',
			},
			{
				displayName: 'Area',
				name: 'area',
				type: 'string',
				default: '',
			},
			{
				displayName: 'Correlation ID',
				name: 'correlationId',
				type: 'string',
				default: '',
				description: 'Shared ID for related events (auto-generated if empty)',
			},
			{
				displayName: 'Source Event ID',
				name: 'sourceEventId',
				type: 'string',
				default: '',
				description: 'Event ID that triggered this event (optional)',
			},

			// ── asset.health fields ──
			{
				displayName: 'Health Index',
				name: 'healthIndex',
				type: 'number',
				default: 1.0,
				typeOptions: { minValue: 0, maxValue: 1, numberPrecision: 2 },
				description: '1.0 = healthy, 0.0 = failed',
				displayOptions: { show: { eventType: ['asset.health'] } },
			},
			{
				displayName: 'Severity',
				name: 'severity',
				type: 'options',
				options: [
					{ name: 'Info', value: 'info' },
					{ name: 'Low', value: 'low' },
					{ name: 'Medium', value: 'medium' },
					{ name: 'High', value: 'high' },
					{ name: 'Critical', value: 'critical' },
				],
				default: 'info',
				displayOptions: { show: { eventType: ['asset.health'] } },
			},
			{
				displayName: 'Condition Trend',
				name: 'conditionTrend',
				type: 'options',
				options: [
					{ name: '(None)', value: '' },
					{ name: 'Worsening', value: 'worsening' },
					{ name: 'Stable', value: 'stable' },
					{ name: 'Improving', value: 'improving' },
				],
				default: '',
				description: 'IAES v1.3 — condition trend direction',
				displayOptions: { show: { eventType: ['asset.health'] } },
			},
			{
				displayName: 'Failure Mode',
				name: 'failureMode',
				type: 'string',
				default: '',
				placeholder: 'bearing_inner_race',
				displayOptions: { show: { eventType: ['asset.health'] } },
			},
			{
				displayName: 'RUL (Days)',
				name: 'rulDays',
				type: 'number',
				default: 0,
				description: 'Remaining useful life in days (0 = not set)',
				displayOptions: { show: { eventType: ['asset.health'] } },
			},
			{
				displayName: 'Recommended Action',
				name: 'recommendedAction',
				type: 'string',
				default: '',
				displayOptions: { show: { eventType: ['asset.health'] } },
			},
			{
				displayName: 'ISO 13374 Status',
				name: 'iso13374Status',
				type: 'options',
				options: [
					{ name: '(None)', value: '' },
					{ name: 'Normal', value: 'normal' },
					{ name: 'Satisfactory', value: 'satisfactory' },
					{ name: 'Unsatisfactory', value: 'unsatisfactory' },
					{ name: 'Unacceptable', value: 'unacceptable' },
					{ name: 'Imminent Failure', value: 'imminent_failure' },
					{ name: 'Failed', value: 'failed' },
				],
				default: '',
				displayOptions: { show: { eventType: ['asset.health'] } },
			},

			// ── asset.measurement fields ──
			{
				displayName: 'Measurement Type',
				name: 'measurementType',
				type: 'options',
				options: [
					{ name: 'Vibration Velocity', value: 'vibration_velocity' },
					{ name: 'Vibration Acceleration', value: 'vibration_acceleration' },
					{ name: 'Temperature', value: 'temperature' },
					{ name: 'Current', value: 'current' },
					{ name: 'Voltage', value: 'voltage' },
					{ name: 'Power', value: 'power' },
					{ name: 'Power Factor', value: 'power_factor' },
					{ name: 'THD Voltage', value: 'thd_voltage' },
					{ name: 'THD Current', value: 'thd_current' },
					{ name: 'Frequency', value: 'frequency' },
					{ name: 'Pressure', value: 'pressure' },
					{ name: 'Flow', value: 'flow' },
					{ name: 'Speed', value: 'speed' },
					{ name: 'Custom', value: 'custom' },
				],
				default: 'vibration_velocity',
				displayOptions: { show: { eventType: ['asset.measurement'] } },
			},
			{
				displayName: 'Value',
				name: 'value',
				type: 'number',
				default: 0,
				typeOptions: { numberPrecision: 4 },
				displayOptions: { show: { eventType: ['asset.measurement'] } },
			},
			{
				displayName: 'Unit',
				name: 'unit',
				type: 'string',
				default: 'mm/s',
				placeholder: 'mm/s, g, °C, A, V',
				displayOptions: { show: { eventType: ['asset.measurement'] } },
			},
			{
				displayName: 'Sensor ID',
				name: 'sensorId',
				type: 'string',
				default: '',
				displayOptions: { show: { eventType: ['asset.measurement'] } },
			},

			// ── work_order_intent fields ──
			{
				displayName: 'Title',
				name: 'woTitle',
				type: 'string',
				default: '',
				required: true,
				placeholder: 'Replace bearing DE side',
				displayOptions: { show: { eventType: ['maintenance.work_order_intent'] } },
			},
			{
				displayName: 'Priority',
				name: 'woPriority',
				type: 'options',
				options: [
					{ name: 'Low', value: 'low' },
					{ name: 'Medium', value: 'medium' },
					{ name: 'High', value: 'high' },
					{ name: 'Emergency', value: 'emergency' },
				],
				default: 'medium',
				displayOptions: { show: { eventType: ['maintenance.work_order_intent'] } },
			},
			{
				displayName: 'Description',
				name: 'woDescription',
				type: 'string',
				typeOptions: { rows: 3 },
				default: '',
				displayOptions: { show: { eventType: ['maintenance.work_order_intent'] } },
			},
			{
				displayName: 'Triggered By',
				name: 'triggeredBy',
				type: 'options',
				options: [
					{ name: 'AI Diagnosis', value: 'ai_diagnosis' },
					{ name: 'Threshold Alert', value: 'threshold' },
					{ name: 'Schedule', value: 'schedule' },
					{ name: 'Manual', value: 'manual' },
				],
				default: 'threshold',
				displayOptions: { show: { eventType: ['maintenance.work_order_intent'] } },
			},
			{
				displayName: 'Recommended Due (Days)',
				name: 'recommendedDueDays',
				type: 'number',
				default: 7,
				displayOptions: { show: { eventType: ['maintenance.work_order_intent'] } },
			},

			// ── maintenance.completion fields ──
			{
				displayName: 'Work Order ID',
				name: 'workOrderId',
				type: 'string',
				default: '',
				required: true,
				displayOptions: { show: { eventType: ['maintenance.completion'] } },
			},
			{
				displayName: 'Completion Status',
				name: 'completionStatus',
				type: 'options',
				options: [
					{ name: 'Completed', value: 'completed' },
					{ name: 'Partially Completed', value: 'partially_completed' },
					{ name: 'Cancelled', value: 'cancelled' },
					{ name: 'Deferred', value: 'deferred' },
				],
				default: 'completed',
				displayOptions: { show: { eventType: ['maintenance.completion'] } },
			},
			{
				displayName: 'Duration (Seconds)',
				name: 'durationSeconds',
				type: 'number',
				default: 0,
				displayOptions: { show: { eventType: ['maintenance.completion'] } },
			},
			{
				displayName: 'Failure Confirmed',
				name: 'failureConfirmed',
				type: 'boolean',
				default: false,
				displayOptions: { show: { eventType: ['maintenance.completion'] } },
			},

			// ── sensor.registration fields ──
			{
				displayName: 'Sensor ID',
				name: 'regSensorId',
				type: 'string',
				default: '',
				required: true,
				displayOptions: { show: { eventType: ['sensor.registration'] } },
			},
			{
				displayName: 'Registration Status',
				name: 'registrationStatus',
				type: 'options',
				options: [
					{ name: 'Discovered', value: 'discovered' },
					{ name: 'Registered', value: 'registered' },
					{ name: 'Calibrated', value: 'calibrated' },
					{ name: 'Decommissioned', value: 'decommissioned' },
				],
				default: 'registered',
				displayOptions: { show: { eventType: ['sensor.registration'] } },
			},

			// ── spare_part_usage fields ──
			{
				displayName: 'Work Order ID',
				name: 'spareWoId',
				type: 'string',
				default: '',
				required: true,
				displayOptions: { show: { eventType: ['maintenance.spare_part_usage'] } },
			},
			{
				displayName: 'Spare Part ID',
				name: 'sparePartId',
				type: 'string',
				default: '',
				required: true,
				displayOptions: { show: { eventType: ['maintenance.spare_part_usage'] } },
			},
			{
				displayName: 'Quantity Used',
				name: 'quantityUsed',
				type: 'number',
				default: 1,
				displayOptions: { show: { eventType: ['maintenance.spare_part_usage'] } },
			},

			// ── Output mode ──
			{
				displayName: 'Output Mode',
				name: 'outputMode',
				type: 'options',
				options: [
					{ name: 'JSON Envelope (Default)', value: 'envelope' },
					{ name: 'Passthrough (Add to Input)', value: 'passthrough' },
				],
				default: 'envelope',
				description: 'How to output the IAES event',
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const results: INodeExecutionData[] = [];

		for (let i = 0; i < items.length; i++) {
			const eventType = this.getNodeParameter('eventType', i) as string;
			const assetId = this.getNodeParameter('assetId', i) as string;
			const source = this.getNodeParameter('source', i) as string;
			const assetName = this.getNodeParameter('assetName', i) as string || undefined;
			const plant = this.getNodeParameter('plant', i) as string || undefined;
			const area = this.getNodeParameter('area', i) as string || undefined;
			const correlationId = this.getNodeParameter('correlationId', i) as string || undefined;
			const sourceEventId = this.getNodeParameter('sourceEventId', i) as string || undefined;
			const outputMode = this.getNodeParameter('outputMode', i) as string;

			const base = { asset_id: assetId, source, asset_name: assetName, plant, area, correlation_id: correlationId, source_event_id: sourceEventId };

			let envelope: IDataObject;

			switch (eventType) {
				case 'asset.health': {
					const event = new AssetHealth({
						...base,
						health_index: this.getNodeParameter('healthIndex', i) as number,
						severity: this.getNodeParameter('severity', i) as string,
						condition_trend: (this.getNodeParameter('conditionTrend', i) as string) || undefined,
						failure_mode: (this.getNodeParameter('failureMode', i) as string) || undefined,
						rul_days: (this.getNodeParameter('rulDays', i) as number) || undefined,
						recommended_action: (this.getNodeParameter('recommendedAction', i) as string) || undefined,
						iso_13374_status: (this.getNodeParameter('iso13374Status', i) as string) || undefined,
					});
					envelope = event.toJSON() as unknown as IDataObject;
					break;
				}
				case 'asset.measurement': {
					const event = new AssetMeasurement({
						...base,
						measurement_type: this.getNodeParameter('measurementType', i) as string,
						value: this.getNodeParameter('value', i) as number,
						unit: this.getNodeParameter('unit', i) as string,
						sensor_id: (this.getNodeParameter('sensorId', i) as string) || undefined,
					});
					envelope = event.toJSON() as unknown as IDataObject;
					break;
				}
				case 'maintenance.work_order_intent': {
					const event = new WorkOrderIntent({
						...base,
						title: this.getNodeParameter('woTitle', i) as string,
						priority: this.getNodeParameter('woPriority', i) as string,
						description: (this.getNodeParameter('woDescription', i) as string) || undefined,
						triggered_by: this.getNodeParameter('triggeredBy', i) as string,
						recommended_due_days: this.getNodeParameter('recommendedDueDays', i) as number,
					});
					envelope = event.toJSON() as unknown as IDataObject;
					break;
				}
				case 'maintenance.completion': {
					const event = new MaintenanceCompletion({
						...base,
						work_order_id: this.getNodeParameter('workOrderId', i) as string,
						status: this.getNodeParameter('completionStatus', i) as string,
						actual_duration_seconds: (this.getNodeParameter('durationSeconds', i) as number) || undefined,
						failure_confirmed: this.getNodeParameter('failureConfirmed', i) as boolean,
					});
					envelope = event.toJSON() as unknown as IDataObject;
					break;
				}
				case 'sensor.registration': {
					const event = new SensorRegistration({
						...base,
						sensor_id: this.getNodeParameter('regSensorId', i) as string,
						registration_status: this.getNodeParameter('registrationStatus', i) as string,
					});
					envelope = event.toJSON() as unknown as IDataObject;
					break;
				}
				case 'maintenance.spare_part_usage': {
					const event = new SparePartUsage({
						...base,
						work_order_id: this.getNodeParameter('spareWoId', i) as string,
						spare_part_id: this.getNodeParameter('sparePartId', i) as string,
						quantity_used: this.getNodeParameter('quantityUsed', i) as number,
					});
					envelope = event.toJSON() as unknown as IDataObject;
					break;
				}
				default:
					throw new Error(`Unknown event type: ${eventType}`);
			}

			if (outputMode === 'passthrough') {
				results.push({
					json: { ...items[i].json, iaes_event: envelope },
				});
			} else {
				results.push({ json: envelope });
			}
		}

		return [results];
	}
}
