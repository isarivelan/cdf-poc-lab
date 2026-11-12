"""Load the local investigation once per data revision."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from maintenance_investigator.paths import config_dir, load_yaml
from maintenance_investigator.pipeline import PipelineResult, run_local_pipeline
from maintenance_investigator.settings import Settings, load_settings


def load_settings_safely(root: Path) -> tuple[Settings | None, str | None]:
    """Return settings or an actionable error string. Secrets are not included."""
    try:
        return load_settings(repo_root=root), None
    except Exception as exc:  # application boundary for the UI
        return None, str(exc)


@st.cache_data(show_spinner=False)
def run_cached_local(root_str: str, _mtime: float) -> PipelineResult:
    """Run the local pipeline. The cache key is the CSV timestamp, not credentials."""
    return run_local_pipeline(Path(root_str))


def sensor_frame(root: Path) -> pd.DataFrame:
    """Read the generated extract."""
    return pd.read_csv(root / "data" / "generated" / "pump_sensor_data.csv")


def app_config(root: Path) -> dict:
    """Read application configuration."""
    return load_yaml(config_dir(root) / "app.yaml")
