"""Generated-data checks."""

from __future__ import annotations

import pytest

from maintenance_investigator.synthetic import generate_wide, to_long
from maintenance_investigator.utils.validation import quality_report

pytestmark = pytest.mark.unit


def test_generated_extract_meets_the_scenario(repo_root) -> None:
    wide, labels = generate_wide()
    long_frame = to_long(wide, labels)
    metrics = quality_report(long_frame, root=repo_root)
    assert metrics["detection_reads_labels"] is False
    assert metrics["missing_percent"] > 0.5
    critical = wide.loc[labels == "critical", "P101_VIBRATION_DE_MM_S"]
    assert float(critical.min()) > 7.1
    shutdown = wide.loc[labels == "shutdown", "M101_MOTOR_SPEED_RPM"]
    assert float(shutdown.max()) < 1
