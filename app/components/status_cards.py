"""Status cards and the decision-support notice."""

from __future__ import annotations

import streamlit as st

from maintenance_investigator.constants import DECISION_SUPPORT_NOTICE


def decision_support_notice() -> None:
    """Show the required decision-support statement."""
    st.info(DECISION_SUPPORT_NOTICE)


def metric_row(items: list[tuple[str, str]]) -> None:
    """Render a row of metrics."""
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items, strict=True):
        column.metric(label, value)


def category_badge(category: str) -> str:
    """Return a short HTML badge for an evidence category."""
    colors = {
        "Observed fact": "#0B6E4F",
        "Historical evidence": "#1D4E89",
        "Manual guidance": "#7A4E00",
        "AI hypothesis": "#6B3FA0",
        "Recommended action": "#8C2F39",
    }
    color = colors.get(category, "#333333")
    return (
        f"<span style='background:{color};color:white;padding:2px 8px;"
        f"border-radius:10px;font-size:0.8rem'>{category}</span>"
    )
