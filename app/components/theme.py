"""Shared presentation for the Streamlit app."""

from __future__ import annotations

import streamlit as st

from maintenance_investigator.constants import DECISION_SUPPORT_NOTICE

APP_NAME = "MaintIQ"
ASSET_LABEL = "Pump P-101"
SITE_LABEL = "Manufacturing Site"


def inject_theme() -> None:
    """Apply layout styles. Call once after page config."""
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1180px; }
        .kicker {
            color: #0B6E4F; font-size: 0.78rem; font-weight: 700;
            letter-spacing: 0.08em; text-transform: uppercase; margin: 0;
        }
        .hero-title { font-size: 2.6rem; line-height: 1.05; margin: 0.15rem 0 0.4rem 0; }
        .lede { color: #3d4a54; font-size: 1.05rem; margin-bottom: 0.6rem; }
        .step-card, .status-card {
            background: #ffffff; border: 1px solid #d9e3de; border-radius: 12px;
            padding: 0.85rem 1rem 0.7rem 1rem; min-height: 7.2rem;
        }
        .step-no { color: #0B6E4F; font-weight: 700; font-size: 0.78rem; letter-spacing: 0.06em; }
        .step-title { font-weight: 700; margin: 0.25rem 0; }
        .step-copy, .status-label { color: #52606d; font-size: 0.92rem; }
        .status-value { font-size: 1.55rem; font-weight: 700; margin: 0.15rem 0; }
        .brand-mark { font-size: 1.25rem; font-weight: 750; color: #14352b; }
        .brand-sub { color: #52606d; margin-bottom: 0.6rem; }
        .quiet-note { color: #52606d; font-size: 0.85rem; margin-top: 1.2rem; }
        div[data-testid="stSidebar"] { background: #eef5f1; }
        a[data-testid="stPageLink-NavLink"] {
            border: 1px solid #0B6E4F; border-radius: 8px; padding: 0.35rem 0.7rem;
            background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def brand_sidebar(mode: str, provider: str) -> None:
    """Show the product name and runtime mode."""
    st.sidebar.markdown(
        f"<div class='brand-mark'>{APP_NAME}</div><div class='brand-sub'>{ASSET_LABEL}</div>",
        unsafe_allow_html=True,
    )
    st.sidebar.caption(f"{mode} · {provider}")


def page_heading(title: str, kicker: str = ASSET_LABEL) -> None:
    """Render a compact page heading."""
    st.markdown(f"<p class='kicker'>{kicker}</p>", unsafe_allow_html=True)
    st.markdown(f"### {title}")


def safety_note() -> None:
    """Show the required decision-support statement without a large banner."""
    st.markdown(
        f"<p class='quiet-note'>{DECISION_SUPPORT_NOTICE}</p>",
        unsafe_allow_html=True,
    )


def status_cards(items: list[tuple[str, str]]) -> None:
    """Render labeled values in a single row of cards."""
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items, strict=True):
        column.markdown(
            "<div class='status-card'>"
            f"<div class='status-label'>{label}</div>"
            f"<div class='status-value'>{value}</div>"
            "</div>",
            unsafe_allow_html=True,
        )
