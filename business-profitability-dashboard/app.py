"""Day 1 starter page; analytics will be added during the project."""

import streamlit as st

st.set_page_config(page_title="Business Profitability Dashboard", layout="wide")
st.title("Business Profitability Dashboard")
st.caption("Retail analytics portfolio project · Planned currency: USD")
st.info("Day 1: Project setup. Data and profitability metrics will be added next.")
st.subheader("Questions this dashboard will answer")
st.markdown(
    "- Which products and categories generate the most gross profit?\n"
    "- Which regions and customer segments have the strongest margins?\n"
    "- How do revenue and gross profit change over time?\n"
    "- Where are discounts associated with low margins or losses?"
)
st.caption("The planned dataset is synthetic. No financial results are available yet.")
