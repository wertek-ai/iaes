/**
 * IAES — Industrial Asset Event Standard
 *
 * A vendor-neutral TypeScript/JavaScript SDK for creating, serializing,
 * and deserializing industrial asset events per the IAES v2.0 specification.
 *
 * @example
 * ```ts
 * import { AssetMeasurement, AssetHealth, Severity } from "iaes";
 *
 * const event = new AssetMeasurement({
 *   asset_id: "MOTOR-001",
 *   measurement_type: "vibration_velocity",
 *   value: 4.2,
 *   unit: "mm/s",
 *   source: "acme.sensors.plant1",
 * });
 *
 * const payload = event.toJSON();
 * console.log(JSON.stringify(payload, null, 2));
 * ```
 */

export {
  SPEC_VERSION,
  SCHEMA_BASE,
  PUBLISHED_EVENT_TYPES,
  schemaUriFor,
  computeContentHash,
} from "./envelope";
export type { IAESEnvelope, IAESWireEnvelope, AssetIdentity } from "./envelope";

export { validate, loadSchema, loadEnvelopeSchema, ValidationError } from "./validation";

export {
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

export {
  AssetMeasurement,
  AssetHealth,
  WorkOrderIntent,
  MaintenanceCompletion,
  AssetHierarchy,
  SensorRegistration,
  SparePartUsage,
  fromObject,
  fromJSON,
} from "./models";

export type {
  AssetMeasurementInit,
  AssetHealthInit,
  WorkOrderIntentInit,
  MaintenanceCompletionInit,
  AssetHierarchyInit,
  SensorRegistrationInit,
  SparePartUsageInit,
} from "./models";

export {
  IaesClient,
  IaesClientError,
  publish,
} from "./client";

export type {
  IaesClientOptions,
  IngestResponse,
} from "./client";
