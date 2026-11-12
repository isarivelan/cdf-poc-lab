"""Maintenance history."""

import streamlit as st
from app.components.page import init_page
from app.components.theme import safety_note

_root, result, _wide = init_page(__file__, "Maintenance history")
if not result.contexts:
    st.info("No incident context is available.")
    st.stop()
labels = [item.incident.external_id for item in result.contexts]
selected = st.selectbox("Incident", labels, index=len(labels) - 1)
context = next(item for item in result.contexts if item.incident.external_id == selected)
st.dataframe(
    [
        {
            "work_order": item.work_order.external_id,
            "equipment": item.work_order.equipment,
            "relevance": item.score,
            "failure_mode": item.work_order.failure_mode,
            "cause": item.work_order.cause,
            "corrective_action": item.work_order.corrective_action,
            "completed": item.work_order.completed_time,
            "relationship": "; ".join(item.reasons),
        }
        for item in context.work_orders
    ],
    hide_index=True,
    width="stretch",
)
safety_note()
