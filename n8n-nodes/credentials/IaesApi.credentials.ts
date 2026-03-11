import type {
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
			default: 'https://api.wertek.ai/api/v1/iaes/ingest',
			placeholder: 'https://your-api.com/iaes/ingest',
			description: 'IAES ingest endpoint URL',
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
			description: 'Bearer token for authentication',
			displayOptions: {
				show: { transport: ['http'] },
			},
		},
		{
			displayName: 'MQTT Broker URL',
			name: 'mqttBroker',
			type: 'string',
			default: 'mqtt://localhost:1883',
			placeholder: 'mqtts://mqtt.wertek.ai:8883',
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
			description: 'Topic prefix (events published to {prefix}/{org_id}/{asset_id}/{event_type})',
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
}
