"""Validate the generated sensor extract."""

from __future__ import annotations

import pandas as pd

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.utils.validation import quality_report


def main() -> None:
    frame = pd.read_csv(ROOT / "data" / "generated" / "pump_sensor_data.csv")
    metrics = quality_report(frame, root=ROOT)
    print(
        "Rows {rows}. Missing {missing_percent}%. Duplicates {duplicate_count}. "
        "Out of range {out_of_range_count}. Labels {labels}.".format(**metrics)
    )


if __name__ == "__main__":
    main()
