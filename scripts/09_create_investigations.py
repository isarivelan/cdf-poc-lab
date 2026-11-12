"""Generate investigations and a local notification payload."""

from __future__ import annotations

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.pipeline import run_local_pipeline


def main() -> None:
    result = run_local_pipeline(ROOT)
    for record in result.investigations:
        print(
            f"{record.external_id} confidence={record.confidence} model={record.model_information}"
        )
    if result.notification:
        print("Notification payload stored at data/local_store/notification.json")
        print(result.notification["title"])


if __name__ == "__main__":
    main()
