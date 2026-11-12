"""Ingest work orders into the local store and, when configured, RAW."""

from __future__ import annotations

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.clients.local_repository import LocalRepository
from maintenance_investigator.ingestion import ingest_work_orders
from maintenance_investigator.settings import load_settings
from maintenance_investigator.synthetic.catalog import work_orders


def main() -> None:
    settings = load_settings(repo_root=ROOT)
    count = ingest_work_orders(LocalRepository(ROOT), work_orders())
    print(f"Upserted {count} local work orders.")
    if settings.cdf_required():
        print("CDF RAW rows are inserted by the development project after the RAW database exists.")
        print("The Toolkit transformation tr_maint_work_orders reads maint_inv_demo.work_orders.")
    else:
        print("APP_MODE is local. RAW was not updated.")


if __name__ == "__main__":
    main()
