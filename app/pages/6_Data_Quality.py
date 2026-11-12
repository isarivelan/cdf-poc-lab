"""Data quality."""

import streamlit as st
from app.components.page import init_page
from app.components.theme import safety_note, status_cards

_root, result, _wide = init_page(__file__, "Data quality")
quality = result.quality
status_cards(
    [
        ("Quality score", str(quality["data_quality_score"])),
        ("Completeness %", str(quality["completeness_percent"])),
        ("Missing %", str(quality["missing_percent"])),
        ("Duplicates", str(quality["duplicate_count"])),
    ]
)
coverage = st.columns(3)
coverage[0].metric("Sensors linked", f"{quality['sensor_link_coverage']}%")
coverage[1].metric("Work orders linked", f"{quality['work_order_link_coverage']}%")
coverage[2].metric("Out of range", str(quality["out_of_range_count"]))
if quality["duplicate_count"] or quality["out_of_range_count"]:
    st.error("Data-quality checks found duplicates or out-of-range values.")
else:
    st.success("No duplicate timestamps and no out-of-range values in the demo extract.")
safety_note()
