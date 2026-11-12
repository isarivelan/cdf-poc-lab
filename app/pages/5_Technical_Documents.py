"""Technical documents."""

import streamlit as st
from app.components.page import init_page
from app.components.theme import safety_note, status_cards

_root, _result, _wide = init_page(__file__, "Technical documents")
manual = _root / "data" / "source" / "maintenance_manual_p101.md"
if not manual.is_file():
    st.error("The maintenance manual is missing. Restore data/source/maintenance_manual_p101.md.")
    st.stop()
text = manual.read_text(encoding="utf-8")
query = st.text_input("Section search", value="SEC-")
status_cards(
    [
        ("Document", "P-101 manual"),
        ("Revision", "Demo-A"),
        ("Linked to", "PUMP-P101"),
        ("Sections", "Parsed"),
    ]
)
for line in text.splitlines():
    if line.startswith("## ") and query.lower() in line.lower():
        st.markdown(f"#### {line.removeprefix('## ')}")
with st.expander("Full manual", expanded=False):
    st.markdown(text)
safety_note()
