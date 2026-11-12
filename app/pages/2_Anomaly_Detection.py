"""Anomaly detection."""

import pandas as pd
import streamlit as st
from app.components.filters import render_filters
from app.components.page import init_page
from app.components.sensor_chart import render_sensor_chart
from app.components.theme import safety_note

_root, result, wide = init_page(__file__, "Anomaly detection")
min_day = wide.index.min().date()
max_day = wide.index.max().date()
sensors, start, end, severities = render_filters(list(wide.columns), min_day, max_day)
mask = (wide.index.date >= start) & (wide.index.date <= end)
window = wide.loc[mask]
selected = [item for item in result.incidents if item.severity in severities]
render_sensor_chart(window, sensors, selected)
st.markdown("#### Rules that held")
if not selected:
    st.info("No incidents match the filters.")
else:
    st.dataframe(
        [
            {
                "incident": item.external_id,
                "severity": item.severity,
                "rules": ", ".join(item.detection_rules),
                "start": item.start_time,
                "end": item.end_time,
                "health_score": item.health_score,
            }
            for item in selected
        ]
    )
critical = next((item for item in result.incidents if item.severity == "critical"), None)
if critical:
    st.markdown("#### Against the earlier baseline")
    rows = []
    for extreme in critical.extremes:
        if extreme.sensor_external_id in sensors:
            rows.append(extreme.model_dump())
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
safety_note()
