import type {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
} from 'n8n-workflow';

/**
 * IAES Lifecycle node — State machine that tracks incident lifecycle.
 *
 * Receives IAES health events and determines the lifecycle phase:
 * - ONSET:      First violation for a (asset_id, rule) pair
 * - ESCALATION: Same incident, severity increased
 * - SUSTAINED:  Same incident, severity unchanged (suppressed by default)
 * - RECOVERY:   Consecutive OK readings after violation
 *
 * Uses n8n workflow static data to persist state across executions.
 */

interface IncidentState {
	correlationId: string;
	assetId: string;
	ruleKey: string;
	currentSeverity: string;
	onsetTimestamp: string;
	lastViolationTimestamp: string;
	consecutiveOkCount: number;
	phase: 'onset' | 'escalation';
}

const SEVERITY_RANK: Record<string, number> = {
	info: 0,
	low: 1,
	medium: 2,
	high: 3,
	critical: 4,
};

function generateId(): string {
	return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export class IaesLifecycle implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'IAES Lifecycle',
		name: 'iaesLifecycle',
		icon: 'file:iaes.svg',
		group: ['transform'],
		version: 1,
		subtitle: 'Incident state machine',
		description: 'Track IAES incident lifecycle — onset, escalation, sustained, recovery',
		defaults: { name: 'IAES Lifecycle' },
		inputs: ['main'],
		outputs: ['main', 'main', 'main'],
		outputNames: ['Onset/Escalation', 'Recovery', 'Suppressed'],
		properties: [
			{
				displayName: 'Input Field',
				name: 'inputField',
				type: 'string',
				default: '',
				description: 'Field containing the IAES event (empty = root of msg.json)',
			},
			{
				displayName: 'Rule Key Field',
				name: 'ruleKeyField',
				type: 'string',
				default: 'data.failure_mode',
				description: 'JSON path to identify the rule/cause (e.g. "data.failure_mode" or "data.measurement_type"). Incidents are tracked per (asset_id, rule_key).',
			},
			{
				displayName: 'OK Severity',
				name: 'okSeverity',
				type: 'string',
				default: 'info',
				description: 'Severity value that means "all clear" (triggers recovery count)',
			},
			{
				displayName: 'Recovery Count',
				name: 'recoveryCount',
				type: 'number',
				default: 3,
				typeOptions: { minValue: 1 },
				description: 'How many consecutive OK events before emitting a recovery',
			},
			{
				displayName: 'Emit Sustained',
				name: 'emitSustained',
				type: 'boolean',
				default: false,
				description: 'When enabled, also emits events for same-severity readings (output 3). When disabled, these are silently suppressed.',
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const onsetEscalation: INodeExecutionData[] = [];
		const recovery: INodeExecutionData[] = [];
		const suppressed: INodeExecutionData[] = [];

		// Persistent state across workflow executions
		const staticData = this.getWorkflowStaticData('node');
		if (!staticData.incidents) {
			staticData.incidents = {};
		}
		const incidents = staticData.incidents as Record<string, IncidentState>;

		for (let i = 0; i < items.length; i++) {
			const inputField = this.getNodeParameter('inputField', i) as string;
			const ruleKeyField = this.getNodeParameter('ruleKeyField', i) as string;
			const okSeverity = this.getNodeParameter('okSeverity', i) as string;
			const recoveryCount = this.getNodeParameter('recoveryCount', i) as number;
			const emitSustained = this.getNodeParameter('emitSustained', i) as boolean;

			// Get the IAES event
			let event: Record<string, unknown>;
			if (inputField && inputField !== '') {
				event = items[i].json[inputField] as Record<string, unknown>;
			} else {
				event = items[i].json;
			}

			if (!event || typeof event !== 'object') {
				continue;
			}

			// Extract key fields
			const asset = event.asset as Record<string, unknown> | undefined;
			const data = event.data as Record<string, unknown> | undefined;
			const assetId = asset?.asset_id as string || event.asset_id as string || '';
			const severity = data?.severity as string || event.severity as string || 'info';
			const timestamp = event.timestamp as string || new Date().toISOString();

			// Extract rule key from dot-path
			let ruleKey = 'default';
			if (ruleKeyField) {
				const parts = ruleKeyField.split('.');
				let current: unknown = event;
				for (const part of parts) {
					if (current && typeof current === 'object') {
						current = (current as Record<string, unknown>)[part];
					} else {
						current = undefined;
						break;
					}
				}
				if (current && typeof current === 'string') {
					ruleKey = current;
				}
			}

			const incidentKey = `${assetId}::${ruleKey}`;
			const isOk = severity === okSeverity;

			if (isOk) {
				// Check if there's an active incident to recover from
				const state = incidents[incidentKey];
				if (state) {
					state.consecutiveOkCount++;
					if (state.consecutiveOkCount >= recoveryCount) {
						// RECOVERY
						recovery.push({
							json: {
								...items[i].json,
								iaes_lifecycle: {
									phase: 'recovery',
									correlation_id: state.correlationId,
									asset_id: assetId,
									rule_key: ruleKey,
									onset_timestamp: state.onsetTimestamp,
									recovery_timestamp: timestamp,
									peak_severity: state.currentSeverity,
									condition_trend: 'improving',
								},
							},
						});
						delete incidents[incidentKey];
					} else if (emitSustained) {
						suppressed.push({
							json: {
								...items[i].json,
								iaes_lifecycle: {
									phase: 'recovering',
									correlation_id: state.correlationId,
									consecutive_ok: state.consecutiveOkCount,
									remaining: recoveryCount - state.consecutiveOkCount,
								},
							},
						});
					}
				}
				// No active incident + OK = nothing to do
			} else {
				// Violation
				const state = incidents[incidentKey];
				if (!state) {
					// ONSET
					const correlationId = event.correlation_id as string || generateId();
					incidents[incidentKey] = {
						correlationId,
						assetId,
						ruleKey,
						currentSeverity: severity,
						onsetTimestamp: timestamp,
						lastViolationTimestamp: timestamp,
						consecutiveOkCount: 0,
						phase: 'onset',
					};
					onsetEscalation.push({
						json: {
							...items[i].json,
							iaes_lifecycle: {
								phase: 'onset',
								correlation_id: correlationId,
								asset_id: assetId,
								rule_key: ruleKey,
								severity,
								condition_trend: 'worsening',
							},
						},
					});
				} else {
					// Active incident — check for escalation
					state.consecutiveOkCount = 0;
					state.lastViolationTimestamp = timestamp;
					const newRank = SEVERITY_RANK[severity] ?? 0;
					const currentRank = SEVERITY_RANK[state.currentSeverity] ?? 0;

					if (newRank > currentRank) {
						// ESCALATION
						state.currentSeverity = severity;
						state.phase = 'escalation';
						onsetEscalation.push({
							json: {
								...items[i].json,
								iaes_lifecycle: {
									phase: 'escalation',
									correlation_id: state.correlationId,
									asset_id: assetId,
									rule_key: ruleKey,
									severity,
									previous_severity: Object.entries(SEVERITY_RANK).find(
										([, v]) => v === currentRank,
									)?.[0],
									condition_trend: 'worsening',
								},
							},
						});
					} else if (emitSustained) {
						// SUSTAINED (same or lower severity)
						suppressed.push({
							json: {
								...items[i].json,
								iaes_lifecycle: {
									phase: 'sustained',
									correlation_id: state.correlationId,
									asset_id: assetId,
									rule_key: ruleKey,
									severity,
								},
							},
						});
					}
				}
			}
		}

		return [onsetEscalation, recovery, suppressed];
	}
}
