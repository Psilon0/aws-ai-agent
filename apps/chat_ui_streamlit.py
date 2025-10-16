import streamlit as st
import json
from src.agent_core import Agent

st.set_page_config(page_title="FinSense Chat", layout="centered")
st.title("💬 FinSense — AI Financial Advisor")

agent = Agent()
if "history" not in st.session_state:
    st.session_state.history = []

with st.form("chat"):
    user_text = st.text_area("Your message", height=120, placeholder="e.g., What's a balanced ETF allocation for 5 years?")
    submitted = st.form_submit_button("Send")

if submitted and user_text.strip():
    payload = {
        "session_id": "st_local",
        "user": {"id": "rafe", "role": "user"},
        "message": {"text": user_text},
        "context": {"locale": "en-GB"}
    }
    out = agent.handle(payload)
    st.session_state.history.append({"user": user_text, "assistant": out})

for turn in st.session_state.history[::-1]:
    st.markdown("**You:** " + turn["user"])
    st.code(json.dumps(turn["assistant"], indent=2), language="json")
