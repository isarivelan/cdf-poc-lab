"""JSON and CSV repository used when CDF credentials are not available."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from maintenance_investigator.exceptions import DataQualityError, ResourceNotFoundError
from maintenance_investigator.models.asset import Asset
from maintenance_investigator.models.document import TechnicalDocument
from maintenance_investigator.models.incident import MaintenanceIncident
from maintenance_investigator.models.investigation import InvestigationRecord
from maintenance_investigator.models.sensor import Sensor
from maintenance_investigator.models.work_order import WorkOrder


def _read_models(path: Path, model: type) -> list:
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [model.model_validate(item) for item in payload]


def _write_models(path: Path, items: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [item.model_dump() for item in items]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _upsert(existing: list, incoming: list) -> list:
    by_id = {item.external_id: item for item in existing}
    for item in incoming:
        by_id[item.external_id] = item
    return list(by_id.values())


class LocalRepository:
    """File-backed store for the local and hybrid demo."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.store = root / "data" / "local_store"
        self.source = root / "data" / "source"
        self.generated = root / "data" / "generated" / "pump_sensor_data.csv"

    def load_sensor_frame(self) -> pd.DataFrame:
        """Load the generated long sensor table."""
        if not self.generated.is_file():
            raise DataQualityError(
                "Generated sensor data was not found.",
                likely_cause=f"Missing {self.generated.name}.",
                action="Run python scripts/01_generate_sample_data.py.",
            )
        frame = pd.read_csv(self.generated)
        if frame.empty:
            raise DataQualityError(
                "Generated sensor data is empty.",
                likely_cause="The CSV has headers but no rows.",
                action="Regenerate sample data.",
            )
        return frame

    def _csv_or_store(self, store_name: str, csv_name: str, model: type) -> list:
        stored = _read_models(self.store / store_name, model)
        if stored:
            return stored
        csv_path = self.source / csv_name
        if not csv_path.is_file():
            raise ResourceNotFoundError(
                f"{csv_name} was not found.",
                likely_cause="Master data has not been generated.",
                action="Run python scripts/01_generate_sample_data.py.",
            )
        frame = pd.read_csv(csv_path).fillna("")
        return [model.model_validate(row) for row in frame.to_dict(orient="records")]

    def list_assets(self) -> list[Asset]:
        """Return assets from the store or the source CSV."""
        return self._csv_or_store("assets.json", "assets.csv", Asset)

    def list_sensors(self) -> list[Sensor]:
        """Return sensors from the store or the source CSV."""
        return self._csv_or_store("sensors.json", "sensors.csv", Sensor)

    def list_work_orders(self) -> list[WorkOrder]:
        """Return work orders from the store or the source CSV."""
        return self._csv_or_store("work_orders.json", "work_orders.csv", WorkOrder)

    def list_documents(self) -> list[TechnicalDocument]:
        """Return stored documents. An empty list means the manual has not been parsed yet."""
        return _read_models(self.store / "documents.json", TechnicalDocument)

    def list_incidents(self) -> list[MaintenanceIncident]:
        """Return stored incidents."""
        return _read_models(self.store / "incidents.json", MaintenanceIncident)

    def list_investigations(self) -> list[InvestigationRecord]:
        """Return stored investigations."""
        return _read_models(self.store / "investigations.json", InvestigationRecord)

    def save_assets(self, assets: list[Asset]) -> None:
        """Upsert assets by external id."""
        _write_models(self.store / "assets.json", _upsert(self.list_assets(), assets))

    def save_sensors(self, sensors: list[Sensor]) -> None:
        """Upsert sensors by external id."""
        _write_models(self.store / "sensors.json", _upsert(self.list_sensors(), sensors))

    def save_work_orders(self, work_orders: list[WorkOrder]) -> None:
        """Upsert work orders by external id."""
        _write_models(
            self.store / "work_orders.json", _upsert(self.list_work_orders(), work_orders)
        )

    def save_documents(self, documents: list[TechnicalDocument]) -> None:
        """Upsert documents by external id."""
        _write_models(self.store / "documents.json", _upsert(self.list_documents(), documents))

    def save_incidents(self, incidents: list[MaintenanceIncident]) -> None:
        """Upsert incidents by external id."""
        _write_models(self.store / "incidents.json", _upsert(self.list_incidents(), incidents))

    def save_investigations(self, investigations: list[InvestigationRecord]) -> None:
        """Upsert investigations by external id."""
        _write_models(
            self.store / "investigations.json",
            _upsert(self.list_investigations(), investigations),
        )

    def save_notification(self, payload: dict[str, object]) -> None:
        """Store a notification payload without sending it."""
        self.store.mkdir(parents=True, exist_ok=True)
        (self.store / "notification.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

    def load_manual_text(self) -> str:
        """Read the synthetic maintenance manual."""
        path = self.source / "maintenance_manual_p101.md"
        if not path.is_file():
            raise ResourceNotFoundError(
                "The maintenance manual was not found.",
                likely_cause=f"Missing {path.name}.",
                action="Restore data/source/maintenance_manual_p101.md.",
            )
        return path.read_text(encoding="utf-8")
