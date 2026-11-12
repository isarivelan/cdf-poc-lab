"""Run rule detection and print incidents."""

from __future__ import annotations

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.pipeline import run_local_pipeline


def main() -> None:
    result = run_local_pipeline(ROOT)
    for incident in result.incidents:
        print(
            f"{incident.external_id} {incident.severity} health={incident.health_score} "
            f"{incident.start_time} -> {incident.end_time}"
        )


if __name__ == "__main__":
    main()
