"""Generate the synthetic Pump P-101 data and the expected incident file."""

from __future__ import annotations

import json

from _bootstrap import bootstrap

ROOT = bootstrap()

from maintenance_investigator.detection.rules import load_rules
from maintenance_investigator.paths import config_dir, load_yaml
from maintenance_investigator.services.incident_service import detect_incidents
from maintenance_investigator.synthetic import write_generated, write_source_files


def main() -> None:
    write_source_files(ROOT)
    frame = write_generated(ROOT)
    rules = load_rules(config_dir(ROOT) / "anomaly_rules.yaml")
    app_config = load_yaml(config_dir(ROOT) / "app.yaml")
    _wide, incidents, _statistical = detect_incidents(frame, app_config=app_config, rules=rules)
    expected = {
        "incidents": [
            {
                "external_id": item.external_id,
                "severity": item.severity,
                "equipment": item.equipment,
                "start_time": item.start_time,
                "end_time": item.end_time,
                "health_score": item.health_score,
                "detection_rules": item.detection_rules,
            }
            for item in incidents
        ]
    }
    target = ROOT / "data" / "expected"
    target.mkdir(parents=True, exist_ok=True)
    (target / "expected_incidents.json").write_text(
        json.dumps(expected, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(frame)} sensor rows and {len(incidents)} expected incidents.")


if __name__ == "__main__":
    main()
