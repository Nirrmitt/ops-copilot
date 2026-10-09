"""Streamlit chat interface for the local FastAPI service."""
import os

import httpx
import streamlit as st

st.set_page_config(page_title="Ops Copilot", page_icon="🛍️")
st.title("Retail Ops Copilot")
question = st.text_area("Ask about a store policy, order, or operations metric")
confirmed = st.checkbox("I confirm any requested ticket action")
if st.button("Ask", type="primary") and question.strip():
    try:
        api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
        response = httpx.post(f"{api_base}/ask", json={"question": question, "confirm": confirmed}, timeout=60)
        response.raise_for_status(); result = response.json()
        st.subheader("Plan"); st.json(result["plan"])
        st.subheader("Tool calls and results")
        for call in result["tool_calls"]: st.json(call)
        st.subheader("Sources"); st.write(result["sources"])
        st.subheader("Answer"); st.write(result["answer"])
        st.metric("Confidence", f"{result['confidence']:.0%}")
        if result["handed_off"]: st.warning("A human should review this request.")
    except httpx.HTTPError as exc:
        st.error(f"The assistant service could not be reached: {exc}")
