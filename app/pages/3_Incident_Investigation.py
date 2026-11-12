"""Incident investigation."""

import streamlit as st
from app.components.evidence_panel import render_evidence
from app.components.page import init_page
from app.components.theme import safety_note, status_cards

_root, result, _wide = init_page(__file__, "Incident investigation")
if not result.investigations:
    st.info("No investigations are available. Generate sample data and refresh.")
    st.stop()
labels = [item.incident for item in result.investigations]
selected = st.selectbox("Incident", labels, index=len(labels) - 1)
record = next(item for item in result.investigations if item.incident == selected)
incident = next(item for item in result.incidents if item.external_id == selected)
context = next(item for item in result.contexts if item.incident.external_id == selected)
status_cards(
    [
        ("Severity", incident.severity),
        ("Health", f"{incident.health_score:.0f}"),
        ("Confidence", f"{record.confidence:.2f}"),
        ("Narrative", "Guided" if record.model_information == "mock" else record.model_information),
    ]
)
st.markdown(f"**{record.response.investigation_summary}**")
render_evidence(record)
st.markdown("#### Similar work")
st.dataframe(
    [
        {
            "work_order": item.work_order.external_id,
            "score": item.score,
            "failure_mode": item.work_order.failure_mode,
            "cause": item.work_order.cause,
            "reasons": "; ".join(item.reasons),
        }
        for item in context.work_orders
    ]
)
st.markdown("#### Manual")
for passage in context.passages:
    st.write(f"**{passage.section_id}** {passage.title} — {passage.relevance_reason}")
    st.caption(passage.passage)
safety_note()
