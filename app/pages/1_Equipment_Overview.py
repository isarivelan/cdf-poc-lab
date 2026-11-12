"""Equipment overview."""

import streamlit as st
from app.components.page import init_page
from app.components.theme import safety_note, status_cards

_root, result, wide = init_page(__file__, "Equipment overview")
open_incidents = [item for item in result.incidents if item.status == "open"]
latest = wide.dropna(how="all").tail(1)
status_cards(
    [
        ("Site", "INDIA Site"),
        ("Health", f"{result.health_score:.0f}"),
        ("Open", str(len(open_incidents))),
        ("Updated", str(result.quality["latest_timestamp"])[5:16].replace("T", " ")),
    ]
)
st.markdown("#### Layout")
places, machines = st.columns(2)
with places:
    st.caption("Location")
    for name in (
        "INDIA Site",
        "Utilities Area",
        "Cooling Water System",
        "PUMP-P101",
    ):
        st.write(name)
with machines:
    st.caption("With the pump")
    for name in ("MOTOR-M101", "VALVE-V101", "BEARING-P101-DE", "BEARING-P101-NDE"):
        st.write(name)

identity, readings = st.columns(2)
with identity:
    st.markdown("#### Pump")
    for label, value in (
        ("Manufacturer", "AquaFlow Industries"),
        ("Model", "CF-200"),
        ("Criticality", "High"),
        ("Status", "Running"),
    ):
        st.write(f"**{label}**  \n{value}")
with readings:
    st.markdown("#### Now")
    if latest.empty:
        st.info("No current readings.")
    else:
        row = latest.iloc[-1]
        shown = [
            ("Drive-end vibration", "P101_VIBRATION_DE_MM_S", "mm/s"),
            ("Drive-end temperature", "P101_BEARING_TEMP_DE_C", "°C"),
            ("Flow", "P101_FLOW_M3_H", "m³/h"),
            ("Motor current", "M101_MOTOR_CURRENT_A", "A"),
        ]
        for label, column, unit in shown:
            value = row.get(column)
            text = "—" if value != value else f"{float(value):.1f} {unit}"
            st.write(f"**{label}**  \n{text}")

st.markdown("#### Incidents")
if not result.incidents:
    st.info("No incidents yet. Generate data and refresh.")
else:
    st.dataframe(
        [
            {
                "Incident": item.external_id,
                "Severity": item.severity,
                "Status": item.status,
                "Health": item.health_score,
                "Start": item.start_time,
            }
            for item in result.incidents
        ],
        hide_index=True,
        width="stretch",
    )
safety_note()
