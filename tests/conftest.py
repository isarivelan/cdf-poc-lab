"""Shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from maintenance_investigator.paths import find_repo_root
from maintenance_investigator.pipeline import PipelineResult, run_local_pipeline
from maintenance_investigator.synthetic import write_generated, write_source_files


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Repository root with generated sample data."""
    root = find_repo_root()
    write_source_files(root)
    if not (root / "data" / "generated" / "pump_sensor_data.csv").is_file():
        write_generated(root)
    return root


@pytest.fixture(scope="session")
def pipeline_result(repo_root: Path) -> PipelineResult:
    """One local pipeline run shared by integration checks."""
    return run_local_pipeline(repo_root)
