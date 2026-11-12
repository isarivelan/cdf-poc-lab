"""Ingest the local asset hierarchy. CDF upserts run only in cdf or hybrid mode."""

from __future__ import annotations

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.clients.local_repository import LocalRepository
from maintenance_investigator.ingestion import ingest_assets
from maintenance_investigator.settings import load_settings
from maintenance_investigator.synthetic.catalog import assets


def main() -> None:
    settings = load_settings(repo_root=ROOT)
    count = ingest_assets(LocalRepository(ROOT), assets())
    print(f"Upserted {count} local assets.")
    if settings.cdf_required():
        print("CDF asset nodes are written by scripts/04 after the Toolkit model is deployed.")
        print("Use the local repository for the demo when the development project is not ready.")


if __name__ == "__main__":
    main()
