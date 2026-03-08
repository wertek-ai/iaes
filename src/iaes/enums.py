"""IAES enumerations — spec-compliant value sets for event fields."""

from enum import Enum


class Severity(str, Enum):
    """Health event severity classification."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MeasurementType(str, Enum):
    """Physical measurement type identifiers."""

    VIBRATION_VELOCITY = "vibration_velocity"
    VIBRATION_ACCELERATION = "vibration_acceleration"
    VIBRATION_DISPLACEMENT = "vibration_displacement"
    TEMPERATURE = "temperature"
    CURRENT = "current"
    VOLTAGE = "voltage"
    POWER = "power"
    ENERGY = "energy"
    PRESSURE = "pressure"
    FLOW = "flow"
    SPEED = "speed"
    POWER_FACTOR = "power_factor"
    THD_VOLTAGE = "thd_voltage"
    THD_CURRENT = "thd_current"
    FREQUENCY = "frequency"
    REACTIVE_POWER = "reactive_power"
    CUSTOM = "custom"


class UnitsQualifier(str, Enum):
    """Signal processing method applied to measurement value (ISO 17359)."""

    RMS = "rms"
    PEAK = "peak"
    PEAK_TO_PEAK = "peak_to_peak"
    AVERAGE = "average"
    TRUE_RMS = "true_rms"


class ISO13374Status(str, Enum):
    """ISO 13374-2 condition status levels."""

    UNKNOWN = "unknown"
    NORMAL = "normal"
    SATISFACTORY = "satisfactory"
    UNSATISFACTORY = "unsatisfactory"
    UNACCEPTABLE = "unacceptable"
    IMMINENT_FAILURE = "imminent_failure"
    FAILED = "failed"


class WorkOrderPriority(str, Enum):
    """Work order priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class CompletionStatus(str, Enum):
    """Work order completion status."""

    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


class HierarchyLevel(str, Enum):
    """Asset hierarchy level."""

    ORGANIZATION = "organization"
    PLANT = "plant"
    AREA = "area"
    EQUIPMENT = "equipment"


class RelationshipType(str, Enum):
    """Hierarchy relationship type."""

    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    SIBLING_OF = "sibling_of"
    DEPENDS_ON = "depends_on"


class RegistrationStatus(str, Enum):
    """Sensor registration lifecycle status."""

    DISCOVERED = "discovered"
    REGISTERED = "registered"
    CALIBRATED = "calibrated"
    DECOMMISSIONED = "decommissioned"
