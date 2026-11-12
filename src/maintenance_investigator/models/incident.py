"""Detected maintenance incidents."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SensorExtreme(BaseModel):
    """Observed extreme and baseline comparison for one sensor."""

    sensor_external_id: str
    unit: str
    minimum: float
    maximum: float
    baseline: float | None = None
    deviation: float | None = None
    trend: str = "flat"


class MaintenanceIncident(BaseModel):
    """An idempotent incident created from sustained anomalies."""

    external_id: str
    title: str
    start_time: str
    end_time: str
    severity: str
    status: str
    equipment: str
    detection_rules: list[str] = Field(default_factory=list)
    health_score: float
    summary: str
    affected_sensors: list[str] = Field(default_factory=list)
    extremes: list[SensorExtreme] = Field(default_factory=list)
    active_minutes: int = 0
    duration_minutes: int = 0
    data_quality_warnings: list[str] = Field(default_factory=list)
    investigation_status: str = "pending"
    detector: str = "rules"
