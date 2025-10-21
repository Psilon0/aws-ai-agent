# PURPOSE: Minimal Streamlit demo for FinSense — collects inputs, runs the pipeline,
#          and displays the advice, allocation, KPIs, and alerts as a chat.
# CONTEXT: Hackathon demo UI for judges; keeps output visible and includes raw JSON.
# CREDITS: Original work — no external code reuse.
# NOTE: Behaviour unchanged; comments only.

import json, time
import streamlit as st
from src.pipeline import run_pipeline

# Basic page metadata for a clean demo layout.
st.set_page_config(page_title="FinSense – Demo", layout="centered")

st.title("FinSense")
st.caption("Autonomous portfolio insights (demo) – not financial advice.")
st.divider()

# Keep a small chat-like history so each run renders as an exchange.
if "history" not in st.session_state:
    st.session_state.history = []

# Simple input controls for risk and horizon; split into two columns for compact UI.
col1, col2 = st.columns(2)
risk = col1.selectbox("Risk profile", ["conservative","moderate","aggressive"], index=1)
horizon = col2.number_input("Horizon (years)", min_value=1, max_value=50, value=5)

# Optional extras: age and a manual “sentiment” knob for demo purposes.
age = st.number_input("Your age (optional)", min_value=16, max_value=100, value=30)
sent_label = st.selectbox("Sentiment (optional)", ["neutral","slightly_bullish","bullish","slightly_bearish","bearish"], index=0)
sent_conf = st.slider("Sentiment confidence", 0.0, 1.0, 0.5, 0.05)

# Run the analytics pipeline and push results into the chat history.
if st.button("Run analysis", type="primary"):
    payload = {"risk_profile": risk, "horizon_years": int(horizon), "age": int(age),
               "sentiment": {"label": sent_label, "confidence": float(sent_conf)},
               "context": {"demo_seed": 123}}
    try:
        t0 = time.time()
        out = run_pipeline(payload)
        st.session_state.history.append(("user", f"Profile={risk}, {horizon}y; sentiment={sent_label}"))
        st.session_state.history.append(("assistant", out))
    except Exception as e:
        st.error(f"Run failed: {e}")

# Render the conversation thread: a user “prompt” followed by structured results.
for role, content in st.session_state.history:
    if role == "user":
        with st.chat_message("user"):
            st.write(content)
    else:
        a = content["advice"]; alloc = content["analytics"]["proposed_allocation"]; k = content["kpis"]
        with st.chat_message("assistant"):
            # Brief summary + one clear next action and disclaimer.
            st.write(a["summary"])
            st.markdown(f"**Action:** {a['one_action']}")
            st.caption(a["disclaimer"])

            # Allocation chart (using Plotly Express for quick, pretty pie).
            st.subheader("Allocation")
            st.plotly_chart(__import__("plotly.express").express.pie(
                names=["Equities","Bonds","Cash"],
                values=[alloc["equities"], alloc["bonds"], alloc["cash"]],
                title="Proposed Allocation"
            ), use_container_width=True)

            # Key metrics at-a-glance.
            st.subheader("KPIs")
            c1,c2,c3 = st.columns(3)
            c1.metric("Exp. Return (1y)", f"{k['exp_return_1y']*100:.1f}%")
            c2.metric("Volatility (1y)", f"{k['exp_vol_1y']*100:.1f}%")
            c3.metric("Max Drawdown", f"{k['max_drawdown']*100:.1f}%")

            # Optional risk alerts (shown only if present).
            alerts = content.get("risk_alerts", [])
            if alerts:
                st.subheader("Risk Alerts")
                for a in alerts:
                    st.warning(f"[{a['severity'].upper()}] {a['type']}: {a['evidence']} — {a['suggested_action']}")

            # Judges often appreciate seeing the raw payload.
            with st.expander("Raw JSON (for judges)"):
                st.code(json.dumps(content, indent=2))
