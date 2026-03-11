/**
 * IAES event models — 7 vendor-neutral classes for the IAES v1.3 spec.
 *
 * Each model produces a spec-compliant IAES envelope via `toJSON()`.
 * All fields are spec-only — no vendor-specific extensions.
 */

import {
  buildEnvelope,
  uuid,
  type AssetIdentity,
  type IAESEnvelope,
} from "./envelope";
import type {
  Severity,
  MeasurementType,
  UnitsQualifier,
  ISO13374Status,
  ConditionTrend,
  WorkOrderPriority,
  CompletionStatus,
  HierarchyLevel,
  RelationshipType,
  RegistrationStatus,
} from "./enums";

// ─── Shared base fields ────────────────────────────────────

interface BaseFields {
  asset_id: string;
  source?: string;
  asset_name?: string | null;
  plant?: string | null;
  area?: string | null;
  event_id?: string;
  correlation_id?: string;
  source_event_id?: string | null;
  batch_id?: string | null;
  timestamp?: string | Date;
  metadata?: Record<string, unknown>;
}

function toISOString(ts?: string | Date): string {
  if (!ts) return new Date().toISOString();
  if (ts instanceof Date) return ts.toISOString();
  return ts;
}

// ─── asset.measurement ─────────────────────────────────────

export interface AssetMeasurementInit extends BaseFields {
  measurement_type: MeasurementType | string;
  value: number;
  unit: string;
  sensor_id?: string | null;
  location?: string | null;
  units_qualifier?: UnitsQualifier | string | null;
  sampling_rate_hz?: number | null;
  acquisition_duration_s?: number | null;
}

export class AssetMeasurement {
  readonly asset_id: string;
  readonly measurement_type: string;
  readonly value: number;
  readonly unit: string;
  readonly source: string;
  readonly sensor_id?: string | null;
  readonly location?: string | null;
  readonly units_qualifier?: string | null;
  readonly sampling_rate_hz?: number | null;
  readonly acquisition_duration_s?: number | null;
  readonly asset_name?: string | null;
  readonly plant?: string | null;
  readonly area?: string | null;
  readonly event_id: string;
  readonly correlation_id: string;
  readonly source_event_id?: string | null;
  readonly batch_id?: string | null;
  readonly timestamp: string;
  readonly metadata: Record<string, unknown>;

  constructor(init: AssetMeasurementInit) {
    this.asset_id = init.asset_id;
    this.measurement_type = init.measurement_type;
    this.value = init.value;
    this.unit = init.unit;
    this.source = init.source ?? "sensors";
    this.sensor_id = init.sensor_id;
    this.location = init.location;
    this.units_qualifier = init.units_qualifier;
    this.sampling_rate_hz = init.sampling_rate_hz;
    this.acquisition_duration_s = init.acquisition_duration_s;
    this.asset_name = init.asset_name;
    this.plant = init.plant;
    this.area = init.area;
    this.event_id = init.event_id ?? uuid();
    this.correlation_id = init.correlation_id ?? uuid();
    this.source_event_id = init.source_event_id;
    this.batch_id = init.batch_id;
    this.timestamp = toISOString(init.timestamp);
    this.metadata = init.metadata ?? {};
  }

  toJSON(): IAESEnvelope {
    return buildEnvelope({
      eventType: "asset.measurement",
      eventId: this.event_id,
      correlationId: this.correlation_id,
      sourceEventId: this.source_event_id,
      batchId: this.batch_id,
      timestamp: this.timestamp,
      source: this.source,
      asset: {
        asset_id: this.asset_id,
        asset_name: this.asset_name,
        plant: this.plant,
        area: this.area,
      },
      data: {
        measurement_type: this.measurement_type,
        value: this.value,
        unit: this.unit,
        sensor_id: this.sensor_id,
        location: this.location,
        units_qualifier: this.units_qualifier,
        sampling_rate_hz: this.sampling_rate_hz,
        acquisition_duration_s: this.acquisition_duration_s,
      },
    });
  }

  static fromJSON(envelope: IAESEnvelope): AssetMeasurement {
    const { asset, data } = envelope;
    return new AssetMeasurement({
      asset_id: asset.asset_id,
      measurement_type: data.measurement_type as string,
      value: data.value as number,
      unit: data.unit as string,
      source: envelope.source,
      sensor_id: data.sensor_id as string | undefined,
      location: data.location as string | undefined,
      units_qualifier: data.units_qualifier as string | undefined,
      sampling_rate_hz: data.sampling_rate_hz as number | undefined,
      acquisition_duration_s: data.acquisition_duration_s as number | undefined,
      asset_name: asset.asset_name,
      plant: asset.plant,
      area: asset.area,
      event_id: envelope.event_id,
      correlation_id: envelope.correlation_id,
      source_event_id: envelope.source_event_id,
      batch_id: envelope.batch_id,
      timestamp: envelope.timestamp,
    });
  }
}

// ─── asset.health ──────────────────────────────────────────

export interface AssetHealthInit extends BaseFields {
  health_index?: number;
  severity?: Severity | string;
  anomaly_score?: number;
  failure_mode?: string | null;
  fault_confidence?: number;
  rul_days?: number | null;
  recommended_action?: string | null;
  estimated_downtime_hours?: number | null;
  iso_13374_status?: ISO13374Status | string | null;
  iso_14224?: Record<string, unknown> | null;
  condition_trend?: ConditionTrend | string | null;
}

export class AssetHealth {
  readonly asset_id: string;
  readonly health_index: number;
  readonly severity: string;
  readonly source: string;
  readonly anomaly_score: number;
  readonly failure_mode?: string | null;
  readonly fault_confidence: number;
  readonly rul_days?: number | null;
  readonly recommended_action?: string | null;
  readonly estimated_downtime_hours?: number | null;
  readonly iso_13374_status?: string | null;
  readonly iso_14224?: Record<string, unknown> | null;
  readonly condition_trend?: string | null;
  readonly asset_name?: string | null;
  readonly plant?: string | null;
  readonly area?: string | null;
  readonly event_id: string;
  readonly correlation_id: string;
  readonly source_event_id?: string | null;
  readonly batch_id?: string | null;
  readonly timestamp: string;
  readonly metadata: Record<string, unknown>;

  constructor(init: AssetHealthInit) {
    this.asset_id = init.asset_id;
    this.health_index = init.health_index ?? 1.0;
    this.severity = init.severity ?? "info";
    this.source = init.source ?? "diagnosis";
    this.anomaly_score = init.anomaly_score ?? 0.0;
    this.failure_mode = init.failure_mode;
    this.fault_confidence = init.fault_confidence ?? 0.0;
    this.rul_days = init.rul_days;
    this.recommended_action = init.recommended_action;
    this.estimated_downtime_hours = init.estimated_downtime_hours;
    this.iso_13374_status = init.iso_13374_status;
    this.iso_14224 = init.iso_14224;
    this.condition_trend = init.condition_trend;
    this.asset_name = init.asset_name;
    this.plant = init.plant;
    this.area = init.area;
    this.event_id = init.event_id ?? uuid();
    this.correlation_id = init.correlation_id ?? uuid();
    this.source_event_id = init.source_event_id;
    this.batch_id = init.batch_id;
    this.timestamp = toISOString(init.timestamp);
    this.metadata = init.metadata ?? {};
  }

  toJSON(): IAESEnvelope {
    return buildEnvelope({
      eventType: "asset.health",
      eventId: this.event_id,
      correlationId: this.correlation_id,
      sourceEventId: this.source_event_id,
      batchId: this.batch_id,
      timestamp: this.timestamp,
      source: this.source,
      asset: {
        asset_id: this.asset_id,
        asset_name: this.asset_name,
        plant: this.plant,
        area: this.area,
      },
      data: {
        health_index: this.health_index,
        anomaly_score: this.anomaly_score,
        severity: this.severity,
        failure_mode: this.failure_mode,
        fault_confidence: this.fault_confidence,
        rul_days: this.rul_days,
        recommended_action: this.recommended_action,
        estimated_downtime_hours: this.estimated_downtime_hours,
        iso_13374_status: this.iso_13374_status,
        iso_14224: this.iso_14224,
        condition_trend: this.condition_trend,
      },
    });
  }

  static fromJSON(envelope: IAESEnvelope): AssetHealth {
    const { asset, data } = envelope;
    return new AssetHealth({
      asset_id: asset.asset_id,
      health_index: data.health_index as number,
      severity: data.severity as string,
      source: envelope.source,
      anomaly_score: data.anomaly_score as number,
      failure_mode: data.failure_mode as string | undefined,
      fault_confidence: data.fault_confidence as number,
      rul_days: data.rul_days as number | undefined,
      recommended_action: data.recommended_action as string | undefined,
      estimated_downtime_hours: data.estimated_downtime_hours as
        | number
        | undefined,
      iso_13374_status: data.iso_13374_status as string | undefined,
      iso_14224: data.iso_14224 as Record<string, unknown> | undefined,
      condition_trend: data.condition_trend as string | undefined,
      asset_name: asset.asset_name,
      plant: asset.plant,
      area: asset.area,
      event_id: envelope.event_id,
      correlation_id: envelope.correlation_id,
      source_event_id: envelope.source_event_id,
      batch_id: envelope.batch_id,
      timestamp: envelope.timestamp,
    });
  }
}

// ─── maintenance.work_order_intent ─────────────────────────

export interface WorkOrderIntentInit extends BaseFields {
  title: string;
  priority?: WorkOrderPriority | string;
  description?: string | null;
  recommended_due_days?: number | null;
  triggered_by?: string | null;
}

export class WorkOrderIntent {
  readonly asset_id: string;
  readonly title: string;
  readonly priority: string;
  readonly source: string;
  readonly description?: string | null;
  readonly recommended_due_days?: number | null;
  readonly triggered_by?: string | null;
  readonly asset_name?: string | null;
  readonly plant?: string | null;
  readonly area?: string | null;
  readonly event_id: string;
  readonly correlation_id: string;
  readonly source_event_id?: string | null;
  readonly batch_id?: string | null;
  readonly timestamp: string;
  readonly metadata: Record<string, unknown>;

  constructor(init: WorkOrderIntentInit) {
    this.asset_id = init.asset_id;
    this.title = init.title;
    this.priority = init.priority ?? "medium";
    this.source = init.source ?? "cmms";
    this.description = init.description;
    this.recommended_due_days = init.recommended_due_days;
    this.triggered_by = init.triggered_by;
    this.asset_name = init.asset_name;
    this.plant = init.plant;
    this.area = init.area;
    this.event_id = init.event_id ?? uuid();
    this.correlation_id = init.correlation_id ?? uuid();
    this.source_event_id = init.source_event_id;
    this.batch_id = init.batch_id;
    this.timestamp = toISOString(init.timestamp);
    this.metadata = init.metadata ?? {};
  }

  toJSON(): IAESEnvelope {
    return buildEnvelope({
      eventType: "maintenance.work_order_intent",
      eventId: this.event_id,
      correlationId: this.correlation_id,
      sourceEventId: this.source_event_id,
      batchId: this.batch_id,
      timestamp: this.timestamp,
      source: this.source,
      asset: {
        asset_id: this.asset_id,
        asset_name: this.asset_name,
        plant: this.plant,
        area: this.area,
      },
      data: {
        title: this.title,
        description: this.description,
        priority: this.priority,
        recommended_due_days: this.recommended_due_days,
        triggered_by: this.triggered_by,
      },
    });
  }

  static fromJSON(envelope: IAESEnvelope): WorkOrderIntent {
    const { asset, data } = envelope;
    return new WorkOrderIntent({
      asset_id: asset.asset_id,
      title: data.title as string,
      priority: data.priority as string,
      source: envelope.source,
      description: data.description as string | undefined,
      recommended_due_days: data.recommended_due_days as number | undefined,
      triggered_by: data.triggered_by as string | undefined,
      asset_name: asset.asset_name,
      plant: asset.plant,
      area: asset.area,
      event_id: envelope.event_id,
      correlation_id: envelope.correlation_id,
      source_event_id: envelope.source_event_id,
      batch_id: envelope.batch_id,
      timestamp: envelope.timestamp,
    });
  }
}

// ─── maintenance.completion ────────────────────────────────

export interface MaintenanceCompletionInit extends BaseFields {
  work_order_id: string;
  status?: CompletionStatus | string;
  actual_duration_seconds?: number | null;
  technician_id?: string | null;
  checklist_completion_pct?: number | null;
  completion_notes?: string | null;
  spare_parts_count?: number | null;
  failure_confirmed?: boolean | null;
  failure_mode?: string | null;
  iso_14224?: Record<string, unknown> | null;
}

export class MaintenanceCompletion {
  readonly asset_id: string;
  readonly work_order_id: string;
  readonly status: string;
  readonly source: string;
  readonly actual_duration_seconds?: number | null;
  readonly technician_id?: string | null;
  readonly checklist_completion_pct?: number | null;
  readonly completion_notes?: string | null;
  readonly spare_parts_count?: number | null;
  readonly failure_confirmed?: boolean | null;
  readonly failure_mode?: string | null;
  readonly iso_14224?: Record<string, unknown> | null;
  readonly asset_name?: string | null;
  readonly plant?: string | null;
  readonly area?: string | null;
  readonly event_id: string;
  readonly correlation_id: string;
  readonly source_event_id?: string | null;
  readonly batch_id?: string | null;
  readonly timestamp: string;
  readonly metadata: Record<string, unknown>;

  constructor(init: MaintenanceCompletionInit) {
    this.asset_id = init.asset_id;
    this.work_order_id = init.work_order_id;
    this.status = init.status ?? "completed";
    this.source = init.source ?? "cmms";
    this.actual_duration_seconds = init.actual_duration_seconds;
    this.technician_id = init.technician_id;
    this.checklist_completion_pct = init.checklist_completion_pct;
    this.completion_notes = init.completion_notes;
    this.spare_parts_count = init.spare_parts_count;
    this.failure_confirmed = init.failure_confirmed;
    this.failure_mode = init.failure_mode;
    this.iso_14224 = init.iso_14224;
    this.asset_name = init.asset_name;
    this.plant = init.plant;
    this.area = init.area;
    this.event_id = init.event_id ?? uuid();
    this.correlation_id = init.correlation_id ?? uuid();
    this.source_event_id = init.source_event_id;
    this.batch_id = init.batch_id;
    this.timestamp = toISOString(init.timestamp);
    this.metadata = init.metadata ?? {};
  }

  toJSON(): IAESEnvelope {
    return buildEnvelope({
      eventType: "maintenance.completion",
      eventId: this.event_id,
      correlationId: this.correlation_id,
      sourceEventId: this.source_event_id,
      batchId: this.batch_id,
      timestamp: this.timestamp,
      source: this.source,
      asset: {
        asset_id: this.asset_id,
        asset_name: this.asset_name,
        plant: this.plant,
        area: this.area,
      },
      data: {
        status: this.status,
        work_order_id: this.work_order_id,
        actual_duration_seconds: this.actual_duration_seconds,
        technician_id: this.technician_id,
        checklist_completion_pct: this.checklist_completion_pct,
        completion_notes: this.completion_notes,
        spare_parts_count: this.spare_parts_count,
        failure_confirmed: this.failure_confirmed,
        failure_mode: this.failure_mode,
        iso_14224: this.iso_14224,
      },
    });
  }

  static fromJSON(envelope: IAESEnvelope): MaintenanceCompletion {
    const { asset, data } = envelope;
    return new MaintenanceCompletion({
      asset_id: asset.asset_id,
      work_order_id: data.work_order_id as string,
      status: data.status as string,
      source: envelope.source,
      actual_duration_seconds: data.actual_duration_seconds as
        | number
        | undefined,
      technician_id: data.technician_id as string | undefined,
      checklist_completion_pct: data.checklist_completion_pct as
        | number
        | undefined,
      completion_notes: data.completion_notes as string | undefined,
      spare_parts_count: data.spare_parts_count as number | undefined,
      failure_confirmed: data.failure_confirmed as boolean | undefined,
      failure_mode: data.failure_mode as string | undefined,
      iso_14224: data.iso_14224 as Record<string, unknown> | undefined,
      asset_name: asset.asset_name,
      plant: asset.plant,
      area: asset.area,
      event_id: envelope.event_id,
      correlation_id: envelope.correlation_id,
      source_event_id: envelope.source_event_id,
      batch_id: envelope.batch_id,
      timestamp: envelope.timestamp,
    });
  }
}

// ─── asset.hierarchy ───────────────────────────────────────

export interface AssetHierarchyInit extends BaseFields {
  hierarchy_level: HierarchyLevel | string;
  relationship_type: RelationshipType | string;
  parent_asset_id?: string | null;
  asset_type?: string | null;
  serial_number?: string | null;
  manufacturer?: string | null;
  model?: string | null;
  location?: string | null;
  is_active?: boolean | null;
}

export class AssetHierarchy {
  readonly asset_id: string;
  readonly hierarchy_level: string;
  readonly relationship_type: string;
  readonly source: string;
  readonly parent_asset_id?: string | null;
  readonly asset_type?: string | null;
  readonly serial_number?: string | null;
  readonly manufacturer?: string | null;
  readonly model?: string | null;
  readonly location?: string | null;
  readonly is_active?: boolean | null;
  readonly asset_name?: string | null;
  readonly plant?: string | null;
  readonly area?: string | null;
  readonly event_id: string;
  readonly correlation_id: string;
  readonly source_event_id?: string | null;
  readonly batch_id?: string | null;
  readonly timestamp: string;
  readonly metadata: Record<string, unknown>;

  constructor(init: AssetHierarchyInit) {
    this.asset_id = init.asset_id;
    this.hierarchy_level = init.hierarchy_level;
    this.relationship_type = init.relationship_type;
    this.source = init.source ?? "hierarchy";
    this.parent_asset_id = init.parent_asset_id;
    this.asset_type = init.asset_type;
    this.serial_number = init.serial_number;
    this.manufacturer = init.manufacturer;
    this.model = init.model;
    this.location = init.location;
    this.is_active = init.is_active;
    this.asset_name = init.asset_name;
    this.plant = init.plant;
    this.area = init.area;
    this.event_id = init.event_id ?? uuid();
    this.correlation_id = init.correlation_id ?? uuid();
    this.source_event_id = init.source_event_id;
    this.batch_id = init.batch_id;
    this.timestamp = toISOString(init.timestamp);
    this.metadata = init.metadata ?? {};
  }

  toJSON(): IAESEnvelope {
    return buildEnvelope({
      eventType: "asset.hierarchy",
      eventId: this.event_id,
      correlationId: this.correlation_id,
      sourceEventId: this.source_event_id,
      batchId: this.batch_id,
      timestamp: this.timestamp,
      source: this.source,
      asset: {
        asset_id: this.asset_id,
        asset_name: this.asset_name,
        plant: this.plant,
        area: this.area,
      },
      data: {
        hierarchy_level: this.hierarchy_level,
        relationship_type: this.relationship_type,
        parent_asset_id: this.parent_asset_id,
        asset_type: this.asset_type,
        serial_number: this.serial_number,
        manufacturer: this.manufacturer,
        model: this.model,
        location: this.location,
        is_active: this.is_active,
      },
    });
  }

  static fromJSON(envelope: IAESEnvelope): AssetHierarchy {
    const { asset, data } = envelope;
    return new AssetHierarchy({
      asset_id: asset.asset_id,
      hierarchy_level: data.hierarchy_level as string,
      relationship_type: data.relationship_type as string,
      source: envelope.source,
      parent_asset_id: data.parent_asset_id as string | undefined,
      asset_type: data.asset_type as string | undefined,
      serial_number: data.serial_number as string | undefined,
      manufacturer: data.manufacturer as string | undefined,
      model: data.model as string | undefined,
      location: data.location as string | undefined,
      is_active: data.is_active as boolean | undefined,
      asset_name: asset.asset_name,
      plant: asset.plant,
      area: asset.area,
      event_id: envelope.event_id,
      correlation_id: envelope.correlation_id,
      source_event_id: envelope.source_event_id,
      batch_id: envelope.batch_id,
      timestamp: envelope.timestamp,
    });
  }
}

// ─── sensor.registration ───────────────────────────────────

export interface SensorRegistrationInit extends BaseFields {
  sensor_id: string;
  registration_status: RegistrationStatus | string;
  sensor_model?: string | null;
  device_serial?: string | null;
  firmware_version?: string | null;
  measurement_capabilities?: string[] | null;
  calibration_date?: string | null;
  communication_protocol?: string | null;
}

export class SensorRegistration {
  readonly asset_id: string;
  readonly sensor_id: string;
  readonly registration_status: string;
  readonly source: string;
  readonly sensor_model?: string | null;
  readonly device_serial?: string | null;
  readonly firmware_version?: string | null;
  readonly measurement_capabilities?: string[] | null;
  readonly calibration_date?: string | null;
  readonly communication_protocol?: string | null;
  readonly asset_name?: string | null;
  readonly plant?: string | null;
  readonly area?: string | null;
  readonly event_id: string;
  readonly correlation_id: string;
  readonly source_event_id?: string | null;
  readonly batch_id?: string | null;
  readonly timestamp: string;
  readonly metadata: Record<string, unknown>;

  constructor(init: SensorRegistrationInit) {
    this.asset_id = init.asset_id;
    this.sensor_id = init.sensor_id;
    this.registration_status = init.registration_status;
    this.source = init.source ?? "sensors";
    this.sensor_model = init.sensor_model;
    this.device_serial = init.device_serial;
    this.firmware_version = init.firmware_version;
    this.measurement_capabilities = init.measurement_capabilities;
    this.calibration_date = init.calibration_date;
    this.communication_protocol = init.communication_protocol;
    this.asset_name = init.asset_name;
    this.plant = init.plant;
    this.area = init.area;
    this.event_id = init.event_id ?? uuid();
    this.correlation_id = init.correlation_id ?? uuid();
    this.source_event_id = init.source_event_id;
    this.batch_id = init.batch_id;
    this.timestamp = toISOString(init.timestamp);
    this.metadata = init.metadata ?? {};
  }

  toJSON(): IAESEnvelope {
    return buildEnvelope({
      eventType: "sensor.registration",
      eventId: this.event_id,
      correlationId: this.correlation_id,
      sourceEventId: this.source_event_id,
      batchId: this.batch_id,
      timestamp: this.timestamp,
      source: this.source,
      asset: {
        asset_id: this.asset_id,
        asset_name: this.asset_name,
        plant: this.plant,
        area: this.area,
      },
      data: {
        sensor_id: this.sensor_id,
        registration_status: this.registration_status,
        sensor_model: this.sensor_model,
        device_serial: this.device_serial,
        firmware_version: this.firmware_version,
        measurement_capabilities: this.measurement_capabilities,
        calibration_date: this.calibration_date,
        communication_protocol: this.communication_protocol,
      },
    });
  }

  static fromJSON(envelope: IAESEnvelope): SensorRegistration {
    const { asset, data } = envelope;
    return new SensorRegistration({
      asset_id: asset.asset_id,
      sensor_id: data.sensor_id as string,
      registration_status: data.registration_status as string,
      source: envelope.source,
      sensor_model: data.sensor_model as string | undefined,
      device_serial: data.device_serial as string | undefined,
      firmware_version: data.firmware_version as string | undefined,
      measurement_capabilities: data.measurement_capabilities as
        | string[]
        | undefined,
      calibration_date: data.calibration_date as string | undefined,
      communication_protocol: data.communication_protocol as
        | string
        | undefined,
      asset_name: asset.asset_name,
      plant: asset.plant,
      area: asset.area,
      event_id: envelope.event_id,
      correlation_id: envelope.correlation_id,
      source_event_id: envelope.source_event_id,
      batch_id: envelope.batch_id,
      timestamp: envelope.timestamp,
    });
  }
}

// ─── maintenance.spare_part_usage ──────────────────────────

export interface SparePartUsageInit extends BaseFields {
  work_order_id: string;
  spare_part_id: string;
  quantity_used: number;
  part_number?: string | null;
  part_name?: string | null;
  unit_cost?: number | null;
  currency?: string | null;
  total_cost?: number | null;
}

export class SparePartUsage {
  readonly asset_id: string;
  readonly work_order_id: string;
  readonly spare_part_id: string;
  readonly quantity_used: number;
  readonly source: string;
  readonly part_number?: string | null;
  readonly part_name?: string | null;
  readonly unit_cost?: number | null;
  readonly currency?: string | null;
  readonly total_cost?: number | null;
  readonly asset_name?: string | null;
  readonly plant?: string | null;
  readonly area?: string | null;
  readonly event_id: string;
  readonly correlation_id: string;
  readonly source_event_id?: string | null;
  readonly batch_id?: string | null;
  readonly timestamp: string;
  readonly metadata: Record<string, unknown>;

  constructor(init: SparePartUsageInit) {
    this.asset_id = init.asset_id;
    this.work_order_id = init.work_order_id;
    this.spare_part_id = init.spare_part_id;
    this.quantity_used = init.quantity_used;
    this.source = init.source ?? "cmms";
    this.part_number = init.part_number;
    this.part_name = init.part_name;
    this.unit_cost = init.unit_cost;
    this.currency = init.currency;
    this.total_cost = init.total_cost;
    this.asset_name = init.asset_name;
    this.plant = init.plant;
    this.area = init.area;
    this.event_id = init.event_id ?? uuid();
    this.correlation_id = init.correlation_id ?? uuid();
    this.source_event_id = init.source_event_id;
    this.batch_id = init.batch_id;
    this.timestamp = toISOString(init.timestamp);
    this.metadata = init.metadata ?? {};
  }

  toJSON(): IAESEnvelope {
    return buildEnvelope({
      eventType: "maintenance.spare_part_usage",
      eventId: this.event_id,
      correlationId: this.correlation_id,
      sourceEventId: this.source_event_id,
      batchId: this.batch_id,
      timestamp: this.timestamp,
      source: this.source,
      asset: {
        asset_id: this.asset_id,
        asset_name: this.asset_name,
        plant: this.plant,
        area: this.area,
      },
      data: {
        work_order_id: this.work_order_id,
        spare_part_id: this.spare_part_id,
        quantity_used: this.quantity_used,
        part_number: this.part_number,
        part_name: this.part_name,
        unit_cost: this.unit_cost,
        currency: this.currency,
        total_cost: this.total_cost,
      },
    });
  }

  static fromJSON(envelope: IAESEnvelope): SparePartUsage {
    const { asset, data } = envelope;
    return new SparePartUsage({
      asset_id: asset.asset_id,
      work_order_id: data.work_order_id as string,
      spare_part_id: data.spare_part_id as string,
      quantity_used: data.quantity_used as number,
      source: envelope.source,
      part_number: data.part_number as string | undefined,
      part_name: data.part_name as string | undefined,
      unit_cost: data.unit_cost as number | undefined,
      currency: data.currency as string | undefined,
      total_cost: data.total_cost as number | undefined,
      asset_name: asset.asset_name,
      plant: asset.plant,
      area: asset.area,
      event_id: envelope.event_id,
      correlation_id: envelope.correlation_id,
      source_event_id: envelope.source_event_id,
      batch_id: envelope.batch_id,
      timestamp: envelope.timestamp,
    });
  }
}

// ─── Dispatch table ────────────────────────────────────────

const EVENT_TYPES: Record<
  string,
  { fromJSON: (e: IAESEnvelope) => unknown }
> = {
  "asset.measurement": AssetMeasurement,
  "asset.health": AssetHealth,
  "maintenance.work_order_intent": WorkOrderIntent,
  "maintenance.completion": MaintenanceCompletion,
  "asset.hierarchy": AssetHierarchy,
  "sensor.registration": SensorRegistration,
  "maintenance.spare_part_usage": SparePartUsage,
};

/**
 * Deserialize any IAES envelope to the corresponding model class.
 * @throws Error if event_type is not recognized
 */
export function fromJSON(envelope: IAESEnvelope): unknown {
  const cls = EVENT_TYPES[envelope.event_type];
  if (!cls) {
    throw new Error(`Unknown IAES event_type: "${envelope.event_type}"`);
  }
  return cls.fromJSON(envelope);
}
