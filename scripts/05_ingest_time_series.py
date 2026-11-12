"""Confirm the sensor extract is available and optionally upload it to CDF."""

from __future__ import annotations

import pandas as pd

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.clients.cdf_client import CdfRepository
from maintenance_investigator.exceptions import MaintenanceInvestigatorError
from maintenance_investigator.settings import assert_development_target, load_settings
from maintenance_investigator.synthetic.catalog import sensors


def main() -> int:
    settings = load_settings(repo_root=ROOT)
    frame = pd.read_csv(ROOT / "data" / "generated" / "pump_sensor_data.csv")
    print(f"Local sensor rows: {len(frame)}")
    if not settings.cdf_required():
        print("APP_MODE is local. Datapoints were not uploaded.")
        return 0
    assert_development_target(settings)
    try:
        repository = CdfRepository(settings)
        data_set_id = repository.ensure_dataset()
        rows = [
            {
                "external_id": item.time_series_external_id,
                "name": item.name,
                "unit": item.unit,
                "description": item.name,
                "equipment": item.equipment,
            }
            for item in sensors()
        ]
        repository.upsert_time_series(rows, data_set_id)
        inserted = repository.insert_datapoints(frame)
        print(f"Uploaded {inserted} datapoints to data set id {data_set_id}.")
    except MaintenanceInvestigatorError as exc:
        print(exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
