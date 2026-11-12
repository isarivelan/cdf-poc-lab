"""Evidence and recommendation panels."""

from __future__ import annotations

import streamlit as st
from app.components.status_cards import category_badge

from maintenance_investigator.models.investigation import InvestigationRecord


def _section(title: str) -> None:
    st.markdown(category_badge(title), unsafe_allow_html=True)


def render_evidence(record: InvestigationRecord) -> None:
    """Show facts, hypotheses, actions, and limitations with category labels."""
    facts, hypotheses = st.columns(2, gap="large")
    with facts:
        _section("Observed fact")
        shown = record.response.observed_facts[:4]
        for fact in shown:
            st.write(f"{fact.fact}")
            st.caption(f"{fact.source_id} · {fact.source_type}")
        extra = record.response.observed_facts[4:]
        if extra:
            with st.expander(f"{len(extra)} more facts"):
                for fact in extra:
                    st.write(fact.fact)
                    st.caption(fact.source_id)
    with hypotheses:
        _section("AI hypothesis")
        for hypothesis in record.response.hypotheses:
            st.write(hypothesis.hypothesis)
            st.caption(f"Confidence {hypothesis.confidence:.2f}")
    st.divider()
    _section("Recommended action")
    for action in record.response.recommended_actions:
        approval = "Needs approval" if action.requires_human_approval else "Missing approval"
        st.write(f"**{action.priority.title()}.** {action.action}")
        st.caption(f"{approval} · {action.source or 'template'}")
    with st.expander("Safety notes and limitations"):
        _section("Manual guidance")
        for note in record.response.safety_notes:
            st.write(note)
        for item in record.response.limitations:
            st.write(item)
