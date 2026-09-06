import type {
	IAuthenticateGeneric,
	ICredentialType,
	INodeProperties,
} from 'n8n-workflow';

export class IaesApi implements ICredentialType {
	name = 'iaesApi';
	displayName = 'IAES API';
	documentationUrl = 'https://iaes.dev';

	properties: INodeProperties[] = [
		{
			displayName: 'Transport',
			name: 'transport',
			type: 'options',
			options: [
				{ name: 'HTTP (REST)', value: 'http' },
				{ name: 'MQTT', value: 'mqtt' },
			],
			default: 'http',
		},
		{
			displayName: 'HTTP Endpoint',
			name: 'httpEndpoint',
			type: 'string',
			// No default host. IAES defines no transport binding, so there is no
			// such thing as "the IAES server" to fall back to -- a default here
			// would either point at somebody's infrastructure or fail silently.
			// The path is the part that is conventional: servers mount the
			// ingest at the root, not under an "/api/v1" prefix.
			default: '',
			required: true,
			placeholder: 'https://your-api.com/iaes/ingest',
			description:
				'IAES ingest endpoint URL. The path is /iaes/ingest — there is no /api/v1 prefix. If you saved this credential before v0.2.0, correct the value by hand: changing the default does not update credentials already stored.',
			displayOptions: {
				show: { transport: ['http'] },
			},
		},
		{
			displayName: 'API Key',
			name: 'apiKey',
			type: 'string',
			typeOptions: { password: true },
			default: '',
			description:
				'Sent as the X-API-Key header (not a Bearer token). The key needs the iaes.ingest scope.',
			displayOptions: {
				show: { transport: ['http'] },
			},
		},
		{
			displayName: 'MQTT Broker URL',
			name: 'mqttBroker',
			type: 'string',
			default: 'mqtt://localhost:1883',
			placeholder: 'mqtts://broker.example.com:8883',
			description: 'MQTT broker connection URL',
			displayOptions: {
				show: { transport: ['mqtt'] },
			},
		},
		{
			displayName: 'MQTT Username',
			name: 'mqttUsername',
			type: 'string',
			default: '',
			displayOptions: {
				show: { transport: ['mqtt'] },
			},
		},
		{
			displayName: 'MQTT Password',
			name: 'mqttPassword',
			type: 'string',
			typeOptions: { password: true },
			default: '',
			displayOptions: {
				show: { transport: ['mqtt'] },
			},
		},
		{
			displayName: 'MQTT Topic Prefix',
			name: 'mqttTopicPrefix',
			type: 'string',
			default: 'iaes',
			description: 'Topic prefix (events published to {prefix}/{asset_id}/{event_type})',
			displayOptions: {
				show: { transport: ['mqtt'] },
			},
		},
		{
			displayName: 'Organization ID',
			name: 'organizationId',
			type: 'string',
			default: '',
			description: 'Your organization identifier (used in MQTT topics and event metadata)',
		},
	];

	// Injects the correct header when this credential is selected on an HTTP
	// Request node. Without it the key had to be wired by hand, and the old
	// description said "Bearer token" — which the ingest rejects with 401.
	authenticate: IAuthenticateGeneric = {
		type: 'generic',
		properties: {
			headers: {
				'X-API-Key': '={{$credentials.apiKey}}',
			},
		},
	};
}
