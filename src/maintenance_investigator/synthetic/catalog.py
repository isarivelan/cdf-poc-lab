"""Fictional master data for the Chennai cooling-water demo."""

from __future__ import annotations

import pandas as pd

from maintenance_investigator.constants import (
    ALL_SENSORS,
    MEASUREMENT_TYPES,
    PRIMARY_EQUIPMENT,
    SENSOR_EQUIPMENT,
    SENSOR_NAMES,
    SENSOR_UNITS,
    SITE_ID,
)
from maintenance_investigator.models.asset import Asset
from maintenance_investigator.models.sensor import Sensor
from maintenance_investigator.models.work_order import WorkOrder


def assets() -> list[Asset]:
    """Return the site, functional locations, and equipment."""
    return [
        Asset(
            external_id=SITE_ID,
            name="Chennai Manufacturing Demo Site",
            entity_type="site",
            description="Synthetic demonstration site. Not a real facility.",
            status="active",
        ),
        Asset(
            external_id="FL-UTILITIES",
            name="Utilities Area",
            entity_type="functional_location",
            description="Utilities functional location for the demo site.",
            parent_external_id=SITE_ID,
            status="active",
        ),
        Asset(
            external_id="FL-CWS",
            name="Cooling Water System",
            entity_type="functional_location",
            description="Cooling water system inside the utilities area.",
            parent_external_id="FL-UTILITIES",
            functional_location="FL-UTILITIES",
            status="active",
        ),
        Asset(
            external_id=PRIMARY_EQUIPMENT,
            name="Cooling Water Pump 101",
            entity_type="equipment",
            description="Centrifugal cooling-water pump. Synthetic demonstration asset.",
            parent_external_id="FL-CWS",
            equipment_type="centrifugal_pump",
            manufacturer="AquaFlow Industries",
            model="CF-200",
            serial_number="SN-P101-DEMO",
            installation_date="2022-04-15",
            criticality="high",
            status="running",
            functional_location="FL-CWS",
        ),
        Asset(
            external_id="MOTOR-M101",
            name="Motor for Pump 101",
            entity_type="equipment",
            description="Induction motor coupled to Pump P-101.",
            parent_external_id="FL-CWS",
            equipment_type="induction_motor",
            manufacturer="Northwind Drives",
            model="ND-160",
            serial_number="SN-M101-DEMO",
            installation_date="2022-04-15",
            criticality="high",
            status="running",
            functional_location="FL-CWS",
        ),
        Asset(
            external_id="VALVE-V101",
            name="Pump discharge valve",
            entity_type="equipment",
            description="Discharge isolation and control valve for Pump P-101.",
            parent_external_id="FL-CWS",
            equipment_type="control_valve",
            manufacturer="Harbor Valve",
            model="HV-90",
            serial_number="SN-V101-DEMO",
            installation_date="2022-04-15",
            criticality="medium",
            status="open",
            functional_location="FL-CWS",
        ),
        Asset(
            external_id="BEARING-P101-DE",
            name="Drive-end bearing",
            entity_type="equipment",
            description="Drive-end rolling-element bearing on Pump P-101.",
            parent_external_id=PRIMARY_EQUIPMENT,
            equipment_type="bearing",
            manufacturer="AquaFlow Industries",
            model="DE-6316",
            serial_number="SN-P101-DE-DEMO",
            installation_date="2025-03-12",
            criticality="high",
            status="installed",
            functional_location="FL-CWS",
        ),
        Asset(
            external_id="BEARING-P101-NDE",
            name="Non-drive-end bearing",
            entity_type="equipment",
            description="Non-drive-end rolling-element bearing on Pump P-101.",
            parent_external_id=PRIMARY_EQUIPMENT,
            equipment_type="bearing",
            manufacturer="AquaFlow Industries",
            model="NDE-6314",
            serial_number="SN-P101-NDE-DEMO",
            installation_date="2022-04-15",
            criticality="medium",
            status="installed",
            functional_location="FL-CWS",
        ),
    ]


def sensors() -> list[Sensor]:
    """Return the ten Pump P-101 demonstration sensors."""
    return [
        Sensor(
            external_id=sensor_id,
            name=SENSOR_NAMES[sensor_id],
            unit=SENSOR_UNITS[sensor_id],
            measurement_type=MEASUREMENT_TYPES[sensor_id],
            equipment=SENSOR_EQUIPMENT[sensor_id],
            time_series_external_id=sensor_id,
        )
        for sensor_id in ALL_SENSORS
    ]


def work_orders() -> list[WorkOrder]:
    """Return historical work orders, including the required P-101 records."""
    return [
        WorkOrder(
            external_id="WO-2025-001",
            title="Replace drive-end bearing",
            description="Drive-end bearing replacement after rising temperature and vibration.",
            work_type="corrective",
            priority="high",
            status="completed",
            opened_time="2025-03-02T06:00:00Z",
            completed_time="2025-03-12T15:00:00Z",
            equipment=PRIMARY_EQUIPMENT,
            failure_mode="Bearing wear",
            cause="Lubrication degradation",
            corrective_action="Bearing replaced, lubrication system inspected",
        ),
        WorkOrder(
            external_id="WO-2025-002",
            title="Pump and motor alignment correction",
            description="Laser alignment after excess vibration on the pump and motor coupling.",
            work_type="corrective",
            priority="high",
            status="completed",
            opened_time="2025-05-20T06:00:00Z",
            completed_time="2025-06-02T11:30:00Z",
            equipment=PRIMARY_EQUIPMENT,
            failure_mode="Excess vibration",
            cause="Coupling misalignment",
            corrective_action="Laser alignment performed",
        ),
        WorkOrder(
            external_id="WO-2025-003",
            title="Investigate reduced cooling-water flow",
            description="Flow shortfall traced to a partially restricted discharge valve.",
            work_type="corrective",
            priority="medium",
            status="completed",
            opened_time="2025-08-11T07:00:00Z",
            completed_time="2025-08-19T16:00:00Z",
            equipment=PRIMARY_EQUIPMENT,
            failure_mode="Low flow",
            cause="Discharge valve partially restricted",
            corrective_action="Valve cleaned and recalibrated",
        ),
        WorkOrder(
            external_id="WO-2025-004",
            title="Routine quarterly inspection",
            description="Quarterly inspection of pump, coupling guard, and lubrication points.",
            work_type="preventive",
            priority="low",
            status="completed",
            opened_time="2025-09-28T06:00:00Z",
            completed_time="2025-09-30T12:00:00Z",
            equipment=PRIMARY_EQUIPMENT,
            failure_mode="None",
            cause="",
            corrective_action="Inspection completed",
        ),
        WorkOrder(
            external_id="WO-2025-005",
            title="Replace motor drive-end bearing",
            description="Motor drive-end bearing replacement after overheating.",
            work_type="corrective",
            priority="high",
            status="completed",
            opened_time="2025-10-21T06:00:00Z",
            completed_time="2025-11-02T14:00:00Z",
            equipment="MOTOR-M101",
            failure_mode="Motor bearing overheating",
            cause="Bearing wear",
            corrective_action="Motor bearing replaced",
        ),
    ]


def failure_events() -> pd.DataFrame:
    """Return a small failure-event table used as additional historical context."""
    rows = [
        {
            "external_id": "FE-2025-001",
            "equipment": PRIMARY_EQUIPMENT,
            "event_time": "2025-03-02T06:10:00Z",
            "failure_mode": "Bearing wear",
            "description": "Drive-end bearing temperature and vibration rose together.",
            "severity": "warning",
        },
        {
            "external_id": "FE-2025-002",
            "equipment": PRIMARY_EQUIPMENT,
            "event_time": "2025-05-20T08:00:00Z",
            "failure_mode": "Excess vibration",
            "description": "Coupling alignment was outside the preferred band.",
            "severity": "warning",
        },
        {
            "external_id": "FE-2025-003",
            "equipment": "MOTOR-M101",
            "event_time": "2025-10-21T09:00:00Z",
            "failure_mode": "Motor bearing overheating",
            "description": "Motor drive-end bearing temperature exceeded the inspection band.",
            "severity": "warning",
        },
    ]
    return pd.DataFrame(rows)


def assets_frame(items: list[Asset] | None = None) -> pd.DataFrame:
    """Serialize assets to a table."""
    return pd.DataFrame([item.model_dump() for item in (items or assets())])


def sensors_frame(items: list[Sensor] | None = None) -> pd.DataFrame:
    """Serialize sensors to a table."""
    return pd.DataFrame([item.model_dump() for item in (items or sensors())])


def work_orders_frame(items: list[WorkOrder] | None = None) -> pd.DataFrame:
    """Serialize work orders to a table."""
    return pd.DataFrame([item.model_dump() for item in (items or work_orders())])
