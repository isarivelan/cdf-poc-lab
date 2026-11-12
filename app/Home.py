"""Pump Desk landing page."""

from app.bootstrap import bootstrap

ROOT = bootstrap(__file__)

import streamlit as st
from app.components.data_loader import load_settings_safely, run_cached_local
from app.components.theme import (
    APP_NAME,
    ASSET_LABEL,
    SITE_LABEL,
    brand_sidebar,
    inject_theme,
    safety_note,
    status_cards,
)

st.set_page_config(page_title=APP_NAME, layout="wide")
inject_theme()
settings, error = load_settings_safely(ROOT)
if settings is not None:
    brand_sidebar(settings.app_mode.value, settings.ai_provider.value)
if error:
    st.error(error)

st.markdown(f"<p class='kicker'>{SITE_LABEL}</p>", unsafe_allow_html=True)
st.markdown(f"<h1 class='hero-title'>{APP_NAME}</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='lede'>Follow Cooling Water Pump 101 from a rising vibration trend "
    "to the checks a person still has to approve.</p>",
    unsafe_allow_html=True,
)
links = st.columns(2)
links[0].page_link("pages/1_Equipment_Overview.py", label="Equipment")
links[1].page_link("pages/3_Incident_Investigation.py", label="Open investigation")

csv_path = ROOT / "data" / "generated" / "pump_sensor_data.csv"
if csv_path.is_file() and settings is not None and error is None:
    result = run_cached_local(str(ROOT), csv_path.stat().st_mtime)
    open_count = sum(item.status == "open" for item in result.incidents)
    critical = next((item for item in result.incidents if item.severity == "critical"), None)
    status_cards(
        [
            ("Health", f"{result.health_score:.0f}"),
            ("Open", str(open_count)),
            ("Asset", ASSET_LABEL),
            ("Window", "Critical" if critical else "Clear"),
        ]
    )
    if critical:
        st.caption(f"{critical.external_id} · health {critical.health_score:.0f}")
else:
    st.warning("Generate the sample history before the status cards can load.")
    st.code("python scripts/01_generate_sample_data.py")

st.markdown("#### Path")
steps = [
    ("01", "Signal", "Vibration, bearing temperature, flow, and motor current."),
    ("02", "Asset", "Pump, motor, valve, and both bearings."),
    ("03", "Record", "Past work orders and the maintenance manual."),
    ("04", "Advice", "A hypothesis, with a check that needs approval."),
]
columns = st.columns(4)
for column, (number, title, copy) in zip(columns, steps, strict=True):
    column.markdown(
        "<div class='step-card'>"
        f"<div class='step-no'>{number}</div>"
        f"<div class='step-title'>{title}</div>"
        f"<div class='step-copy'>{copy}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
safety_note()
