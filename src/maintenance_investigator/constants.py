"""Stable identifiers and engineering constants for the Pump P-101 demo."""

from __future__ import annotations

PRIMARY_EQUIPMENT = "PUMP-P101"
SITE_ID = "SITE-CHN-DEMO"
RANDOM_SEED = 42

VIB_DE = "P101_VIBRATION_DE_MM_S"
VIB_NDE = "P101_VIBRATION_NDE_MM_S"
TEMP_DE = "P101_BEARING_TEMP_DE_C"
TEMP_NDE = "P101_BEARING_TEMP_NDE_C"
DISCHARGE_P = "P101_DISCHARGE_PRESSURE_BAR"
SUCTION_P = "P101_SUCTION_PRESSURE_BAR"
FLOW = "P101_FLOW_M3_H"
CURRENT = "M101_MOTOR_CURRENT_A"
SPEED = "M101_MOTOR_SPEED_RPM"
VALVE = "V101_VALVE_POSITION_PCT"

SENSOR_UNITS: dict[str, str] = {
    VIB_DE: "mm/s",
    VIB_NDE: "mm/s",
    TEMP_DE: "C",
    TEMP_NDE: "C",
    DISCHARGE_P: "bar",
    SUCTION_P: "bar",
    FLOW: "m3/h",
    CURRENT: "A",
    SPEED: "rpm",
    VALVE: "%",
}

SENSOR_EQUIPMENT: dict[str, str] = {
    VIB_DE: "BEARING-P101-DE",
    VIB_NDE: "BEARING-P101-NDE",
    TEMP_DE: "BEARING-P101-DE",
    TEMP_NDE: "BEARING-P101-NDE",
    DISCHARGE_P: PRIMARY_EQUIPMENT,
    SUCTION_P: PRIMARY_EQUIPMENT,
    FLOW: PRIMARY_EQUIPMENT,
    CURRENT: "MOTOR-M101",
    SPEED: "MOTOR-M101",
    VALVE: "VALVE-V101",
}

SENSOR_NAMES: dict[str, str] = {
    VIB_DE: "Pump P-101 drive-end vibration",
    VIB_NDE: "Pump P-101 non-drive-end vibration",
    TEMP_DE: "Pump P-101 drive-end bearing temperature",
    TEMP_NDE: "Pump P-101 non-drive-end bearing temperature",
    DISCHARGE_P: "Pump P-101 discharge pressure",
    SUCTION_P: "Pump P-101 suction pressure",
    FLOW: "Pump P-101 flow",
    CURRENT: "Motor M-101 current",
    SPEED: "Motor M-101 speed",
    VALVE: "Valve V-101 position",
}

MEASUREMENT_TYPES: dict[str, str] = {
    VIB_DE: "vibration",
    VIB_NDE: "vibration",
    TEMP_DE: "temperature",
    TEMP_NDE: "temperature",
    DISCHARGE_P: "pressure",
    SUCTION_P: "pressure",
    FLOW: "flow",
    CURRENT: "current",
    SPEED: "speed",
    VALVE: "position",
}

ALL_SENSORS: tuple[str, ...] = tuple(SENSOR_UNITS)

DECISION_SUPPORT_NOTICE = (
    "POC decision-support output. Verify evidence and follow approved site "
    "safety and maintenance procedures before taking action."
)

SYNTHETIC_BANNER = (
    "SYNTHETIC DEMONSTRATION CONTENT. This manual describes fictional equipment "
    "at the Chennai Manufacturing Demo Site and must not be used for real maintenance."
)
