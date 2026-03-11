/** IAES enumerations — spec-compliant value sets for event fields. */

export const Severity = {
  INFO: "info",
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high",
  CRITICAL: "critical",
} as const;
export type Severity = (typeof Severity)[keyof typeof Severity];

export const MeasurementType = {
  VIBRATION_VELOCITY: "vibration_velocity",
  VIBRATION_ACCELERATION: "vibration_acceleration",
  VIBRATION_DISPLACEMENT: "vibration_displacement",
  TEMPERATURE: "temperature",
  CURRENT: "current",
  VOLTAGE: "voltage",
  POWER: "power",
  ENERGY: "energy",
  PRESSURE: "pressure",
  FLOW: "flow",
  SPEED: "speed",
  POWER_FACTOR: "power_factor",
  THD_VOLTAGE: "thd_voltage",
  THD_CURRENT: "thd_current",
  FREQUENCY: "frequency",
  REACTIVE_POWER: "reactive_power",
  CUSTOM: "custom",
} as const;
export type MeasurementType =
  (typeof MeasurementType)[keyof typeof MeasurementType];

export const UnitsQualifier = {
  RMS: "rms",
  PEAK: "peak",
  PEAK_TO_PEAK: "peak_to_peak",
  AVERAGE: "average",
  TRUE_RMS: "true_rms",
} as const;
export type UnitsQualifier =
  (typeof UnitsQualifier)[keyof typeof UnitsQualifier];

export const ISO13374Status = {
  UNKNOWN: "unknown",
  NORMAL: "normal",
  SATISFACTORY: "satisfactory",
  UNSATISFACTORY: "unsatisfactory",
  UNACCEPTABLE: "unacceptable",
  IMMINENT_FAILURE: "imminent_failure",
  FAILED: "failed",
} as const;
export type ISO13374Status =
  (typeof ISO13374Status)[keyof typeof ISO13374Status];

export const ConditionTrend = {
  WORSENING: "worsening",
  STABLE: "stable",
  IMPROVING: "improving",
} as const;
export type ConditionTrend =
  (typeof ConditionTrend)[keyof typeof ConditionTrend];

export const WorkOrderPriority = {
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high",
  EMERGENCY: "emergency",
} as const;
export type WorkOrderPriority =
  (typeof WorkOrderPriority)[keyof typeof WorkOrderPriority];

export const CompletionStatus = {
  COMPLETED: "completed",
  PARTIALLY_COMPLETED: "partially_completed",
  CANCELLED: "cancelled",
  DEFERRED: "deferred",
} as const;
export type CompletionStatus =
  (typeof CompletionStatus)[keyof typeof CompletionStatus];

export const HierarchyLevel = {
  ORGANIZATION: "organization",
  PLANT: "plant",
  AREA: "area",
  EQUIPMENT: "equipment",
} as const;
export type HierarchyLevel =
  (typeof HierarchyLevel)[keyof typeof HierarchyLevel];

export const RelationshipType = {
  PARENT_OF: "parent_of",
  CHILD_OF: "child_of",
  SIBLING_OF: "sibling_of",
  DEPENDS_ON: "depends_on",
} as const;
export type RelationshipType =
  (typeof RelationshipType)[keyof typeof RelationshipType];

export const RegistrationStatus = {
  DISCOVERED: "discovered",
  REGISTERED: "registered",
  CALIBRATED: "calibrated",
  DECOMMISSIONED: "decommissioned",
} as const;
export type RegistrationStatus =
  (typeof RegistrationStatus)[keyof typeof RegistrationStatus];
