"""Data-quality metrics for the demo extract and its links."""

from __future__ import annotations

from typing import Any

import pandas as pd

from maintenance_investigator.constants import ALL_SENSORS
from maintenance_investigator.models.asset import Asset
from maintenance_investigator.models.document import TechnicalDocument
from maintenance_investigator.models.incident import MaintenanceIncident
from maintenance_investigator.models.sensor import Sensor
from maintenance_investigator.models.work_order import WorkOrder


def data_quality_report(
    frame: pd.DataFrame,
    *,
    assets: list[Asset],
    sensors: list[Sensor],
    work_orders: list[WorkOrder],
    documents: list[TechnicalDocument],
    incidents: list[MaintenanceIncident],
    ranges: dict[str, list[float]],
) -> dict[str, Any]:
    """Summarize completeness, ranges, staleness, and link coverage."""
    stamped = pd.to_datetime(frame["timestamp"], utc=True)
    expected = stamped.nunique() * len(ALL_SENSORS)
    duplicates = int(frame.duplicated(["timestamp", "sensor_external_id"]).sum())
    missing_percent = 100.0 * (expected - len(frame)) / expected if expected else 0.0
    out_of_range = 0
    for sensor, bounds in ranges.items():
        values = frame.loc[frame["sensor_external_id"] == sensor, "value"]
        if values.empty:
            continue
        out_of_range += int(((values < bounds[0]) | (values > bounds[1])).sum())
    latest = stamped.max()
    earliest = stamped.min()
    asset_ids = {asset.external_id for asset in assets}
    linked_sensors = sum(1 for sensor in sensors if sensor.equipment in asset_ids)
    linked_orders = sum(1 for order in work_orders if order.equipment in asset_ids)
    linked_documents = sum(
        1 for document in documents if document.equipment in asset_ids and document.sections
    )
    linked_incidents = sum(1 for incident in incidents if incident.equipment in asset_ids)
    sensor_coverage = 100.0 * linked_sensors / len(sensors) if sensors else 0.0
    order_coverage = 100.0 * linked_orders / len(work_orders) if work_orders else 0.0
    document_coverage = 100.0 * linked_documents / len(documents) if documents else 0.0
    penalties = min(40.0, missing_percent * 5) + min(30.0, duplicates * 5) + min(30.0, out_of_range)
    score = round(max(0.0, 100.0 - penalties), 1)
    return {
        "rows": int(len(frame)),
        "completeness_percent": round(100.0 - missing_percent, 3),
        "missing_percent": round(missing_percent, 3),
        "duplicate_count": duplicates,
        "out_of_range_count": out_of_range,
        "latest_timestamp": latest.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "earliest_timestamp": earliest.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "staleness_minutes": 0,
        "sensor_link_coverage": round(sensor_coverage, 1),
        "work_order_link_coverage": round(order_coverage, 1),
        "document_link_coverage": round(document_coverage, 1),
        "incident_link_coverage": round(100.0 * linked_incidents / len(incidents), 1)
        if incidents
        else 0.0,
        "unlinked_sensors": len(sensors) - linked_sensors,
        "unlinked_work_orders": len(work_orders) - linked_orders,
        "data_quality_score": score,
    }
