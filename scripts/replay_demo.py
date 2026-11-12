"""Replay the final anomaly window without printing credentials."""

from __future__ import annotations

import argparse
import time

import pandas as pd

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.constants import VIB_DE


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay the Pump P-101 critical window.")
    parser.add_argument("--speed", type=float, default=60.0, help="Minutes of data per second.")
    parser.add_argument(
        "--max-steps", type=int, default=0, help="Stop after this many printed steps."
    )
    args = parser.parse_args()
    frame = pd.read_csv(ROOT / "data" / "generated" / "pump_sensor_data.csv")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    window = frame.loc[frame["timestamp"] >= "2026-11-11T20:00:00Z"]
    grouped = window.groupby("timestamp")
    delay = 0.0 if args.speed <= 0 else 60.0 / args.speed
    for step, (stamp, rows) in enumerate(grouped, start=1):
        vibration = rows.loc[rows["sensor_external_id"] == VIB_DE, "value"]
        value = float(vibration.iloc[0]) if not vibration.empty else float("nan")
        print(f"{stamp.strftime('%Y-%m-%dT%H:%M:%SZ')} drive-end vibration {value:.2f} mm/s")
        if args.max_steps and step >= args.max_steps:
            break
        if delay:
            time.sleep(delay)


if __name__ == "__main__":
    main()
