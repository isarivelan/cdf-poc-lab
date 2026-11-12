"""Plotly sensor trends with thresholds and incident windows."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from maintenance_investigator.models.incident import MaintenanceIncident

_THRESHOLDS = {
    "P101_VIBRATION_DE_MM_S": [(4.5, "warning"), (7.1, "critical")],
    "P101_BEARING_TEMP_DE_C": [(75, "warning"), (82, "critical")],
    "P101_FLOW_M3_H": [(88, "warning"), (82, "critical")],
    "M101_MOTOR_CURRENT_A": [(44, "warning")],
}


def render_sensor_chart(
    wide: pd.DataFrame,
    sensors: list[str],
    incidents: list[MaintenanceIncident],
) -> None:
    """Draw selected sensors and shade incident windows."""
    if wide.empty or not sensors:
        st.warning("No sensor data in the selected range.")
        return
    figure = go.Figure()
    for sensor in sensors:
        if sensor not in wide.columns:
            continue
        figure.add_trace(go.Scatter(x=wide.index, y=wide[sensor], name=sensor, mode="lines"))
        for value, name in _THRESHOLDS.get(sensor, []):
            figure.add_hline(y=value, line_dash="dot", annotation_text=f"{sensor} {name} {value}")
    for incident in incidents:
        color = (
            "rgba(140,47,57,0.15)" if incident.severity == "critical" else "rgba(184,132,0,0.15)"
        )
        figure.add_vrect(
            x0=incident.start_time, x1=incident.end_time, fillcolor=color, line_width=0
        )
    figure.update_layout(
        height=460, legend_orientation="h", margin={"l": 40, "r": 20, "t": 30, "b": 40}
    )
    st.plotly_chart(figure, width="stretch")
