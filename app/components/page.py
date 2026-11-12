"""Page setup shared by the Streamlit workflow."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from app.bootstrap import bootstrap
from app.components.data_loader import load_settings_safely, run_cached_local, sensor_frame
from app.components.theme import APP_NAME, brand_sidebar, inject_theme, page_heading

from maintenance_investigator.clients.cdf_client import probe_connection
from maintenance_investigator.ingestion.time_series import to_wide
from maintenance_investigator.pipeline import PipelineResult


def init_page(start_file: str, title: str) -> tuple[Path, PipelineResult, pd.DataFrame]:
    """Configure a page, show the mode, and return the local investigation."""
    root = bootstrap(start_file)
    st.set_page_config(page_title=f"{title} · {APP_NAME}", layout="wide")
    inject_theme()
    settings, error = load_settings_safely(root)
    if error or settings is None:
        st.sidebar.error("Configuration")
        st.error(error or "Configuration failed.")
        st.stop()
    brand_sidebar(settings.app_mode.value, settings.ai_provider.value)
    if settings.ai_fallback_reason:
        st.sidebar.caption(settings.ai_fallback_reason)
    if settings.cdf_required():
        status, detail = probe_connection(settings)
        if status == "ok":
            st.sidebar.success("Connected")
        else:
            st.sidebar.error("Not connected")
            st.error(detail)
            st.stop()
        st.caption("Signed in. Charts on this demo still use the local sensor extract.")
    csv_path = root / "data" / "generated" / "pump_sensor_data.csv"
    if not csv_path.is_file():
        st.warning("Sample data has not been generated.")
        st.code("python scripts/01_generate_sample_data.py")
        st.stop()
    if st.sidebar.button("Refresh data"):
        st.cache_data.clear()
    result = run_cached_local(str(root), csv_path.stat().st_mtime)
    frame = sensor_frame(root)
    wide = to_wide(frame)
    page_heading(title)
    return root, result, wide
