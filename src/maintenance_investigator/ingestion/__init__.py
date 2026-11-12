"""Idempotent master-data writes through a repository."""

from __future__ import annotations

from typing import Protocol

from maintenance_investigator.models.asset import Asset
from maintenance_investigator.models.document import TechnicalDocument
from maintenance_investigator.models.sensor import Sensor
from maintenance_investigator.models.work_order import WorkOrder


class SupportsMasterData(Protocol):
    """Repositories that can upsert demonstration master data."""

    def save_assets(self, assets: list[Asset]) -> None:
        """Replace assets by external id."""

    def save_sensors(self, sensors: list[Sensor]) -> None:
        """Replace sensors by external id."""

    def save_work_orders(self, work_orders: list[WorkOrder]) -> None:
        """Replace work orders by external id."""

    def save_documents(self, documents: list[TechnicalDocument]) -> None:
        """Replace documents by external id."""


def ingest_assets(repository: SupportsMasterData, assets: list[Asset]) -> int:
    """Upsert assets and return the count."""
    repository.save_assets(assets)
    return len(assets)


def ingest_sensors(repository: SupportsMasterData, sensors: list[Sensor]) -> int:
    """Upsert sensors and return the count."""
    repository.save_sensors(sensors)
    return len(sensors)


def ingest_work_orders(repository: SupportsMasterData, work_orders: list[WorkOrder]) -> int:
    """Upsert work orders and return the count."""
    repository.save_work_orders(work_orders)
    return len(work_orders)


def ingest_documents(repository: SupportsMasterData, documents: list[TechnicalDocument]) -> int:
    """Upsert documents and return the count."""
    repository.save_documents(documents)
    return len(documents)
