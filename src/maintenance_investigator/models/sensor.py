"""Sensor catalog records."""

from __future__ import annotations

from pydantic import BaseModel


class Sensor(BaseModel):
    """A measurement point linked to equipment and a CDF time series."""

    external_id: str
    name: str
    unit: str
    measurement_type: str
    equipment: str
    time_series_external_id: str
