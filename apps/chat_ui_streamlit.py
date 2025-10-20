import re
from typing import Dict, Any
import requests
import streamlit as st
import matplotlib.pyplot as plt

# =========================
# Streamlit Setup
# =========================
st.set_page_config(
    page_title="Portfolio Recommendation Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Sidebar Configuration
# =========================
st.sidebar.header("Configuration")
if "age_sb" not in st.session_state:
    st.session_state.age_sb = 25
if "risk_sb" not in st.session_state:
    st.session_state.risk_sb = "moderate"
if "horizon_sb" not in st.session_state:
    st.session_state.horizon_sb = 5

# --- your live API endpoint here ---
api_base = st.sidebar.text_input("API Base URL", "https://vk2cpxrtac.execute-api.eu-west-2.amazonaws.com")
age = st.sidebar.number_input("Age", min_value=16, max_value=100, value=st.session_state.age_sb, key="age_sb")
risk = st.sidebar.selectbox(
    "Risk Profile", 
    ["conservative", "moderate", "aggressive"], 
    index=1, 
    key="risk_sb",
    help="‘moderate’ maps to ‘balanced’ for the API"
)
horizon = st.sidebar.number_input("Horizon (years)", min_value=1, max_value=40, value=st.session_state.horizon_sb, key="horizon_sb")
demo_seed = st.sidebar.text_input("Demo Seed (optional)", "")
force_high_vol = st.sidebar.checkbox("Force high volatility (demo)", False)
use_sidebar = st.sidebar.checkbox("Use sidebar as override", False)
reset = st.sidebar.button("New session")

# =========================
# Chat State
# =========================
if reset or "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help? Try: “I am 25, moderate risk, 5-year horizon.”"}]
if "amount_gbp_override" not in st.session_state:
    st.session_state.amount_gbp_override = None
if "percent_intent" not in st.session_state:
    st.session_state.percent_intent = None

# =========================
# Helper: Parse Text Overrides
# =========================
def parse_overrides(text: str) -> dict:
    text_l = text.lower()
    out: Dict[str, Any] = {}
    m_h = re.search(r"\b(1|[2-3]?\d)\s*(?:y|yr|yrs|year|years)\b", text_l)
    if m_h:
        out["horizon_years"] = int(m_h.group(1))
    if re.search(r"\b(high\s*risk|aggressive)\b", text_l):
        out["risk"] = "aggressive"
    elif re.search(r"\b(moderate|balanced)\b", text_l):
        out["risk"] = "moderate"
    elif re.search(r"\b(low\s*risk|conservative)\b", text_l):
        out["risk"] = "conservative"
    m_amt = re.search(r"£\s*([0-9]+(?:\.[0-9]{1,2})?)", text_l)
    if m_amt:
        out["amount_gbp"] = float(m_amt.group(1))
    return out

# =========================
# Helper: Call Deployed /run API
# =========================
def call_api(message: str) -> Dict[str, Any]:
    risk_map = {"conservative": "conservative", "moderate": "balanced", "aggressive": "aggressive"}
    risk_profile = risk_map.get(st.session_state.get("risk_sb", "moderate"), "balanced")
    horizon_years = int(st.session_state.get("horizon_sb", 5))
    overrides = parse_overrides(message)
    if "risk" in overrides:
        risk_profile = risk_map.get(overrides["risk"], overrides["risk"])
    if "horizon_years" in overrides:
        horizon_years = overrides["horizon_years"]
    st.session_state["amount_gbp_override"] = overrides.get("amount_gbp")
    seed_val = 42
    if demo_seed.strip():
        try:
            seed_val = int(demo_seed.strip())
        except ValueError:
            pass
    payload = {
        "risk_profile": risk_profile,
        "horizon_years": horizon_years,
        "context": {"demo_seed": seed_val}
    }
    r = requests.post(f"{api_base.rstrip('/')}/run", json=payload, timeout=15)
    r.raise_for_status()
    return payload, r.json()

# =========================
# Display Helpers
# =========================
def allocation_pie(allocation: Dict[str, float]):
    labels = ["Equities", "Bonds", "Cash"]
    values = [allocation.get("equities", 0), allocation.get("bonds", 0), allocation.get("cash", 0)]
    fig, ax = plt.subplots()
    ax.pie(values, labels=[f"{l} ({v*100:.1f}%)" for l, v in zip(labels, values)], autopct=lambda p: f"{p:.1f}%")
    ax.axis("equal")
    st.pyplot(fig, clear_figure=True)

def amount_breakdown_gbp(amount: float, alloc: dict) -> dict:
    return {
        "Equities (£)": round(amount * alloc.get("equities", 0), 2),
        "Bonds (£)": round(amount * alloc.get("bonds", 0), 2),
        "Cash (£)": round(amount * alloc.get("cash", 0), 2),
    }

# =========================
# Chat UI
# =========================
st.title("FinSense — Portfolio Advisor")
st.caption(f"Backend: {api_base.rstrip('/')}/run")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Ask something like: “I'm 25, moderate risk, 5 years.”")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    try:
        payload, data = call_api(prompt)
    except requests.exceptions.RequestException as e:
        msg = f"API request failed: {e}"
        st.session_state.messages.append({"role": "assistant", "content": msg})
        with st.chat_message("assistant"):
            st.error(msg)
    else:
        advice = data.get("advice", {})
        allocation = data.get("allocation", {})
        kpis = data.get("kpis", {})
        with st.chat_message("assistant"):
            st.subheader("Advice")
            st.write(advice.get("summary", "No summary available."))
            st.caption(advice.get("disclaimer", ""))
            st.markdown("---")
            col1, col2 = st.columns([2, 1], gap="large")
            with col1:
                if allocation:
                    allocation_pie(allocation)
                    amt = st.session_state.get("amount_gbp_override")
                    if isinstance(amt, (int, float)):
                        st.markdown("**Investment Breakdown (GBP)**")
                        st.table(amount_breakdown_gbp(amt, allocation))
                else:
                    st.info("No allocation data available.")
            with col2:
                st.metric("Expected 1Y Return", f"{kpis.get('exp_return_1y',0)*100:.1f}%")
                st.metric("Volatility (Ann.)", f"{kpis.get('exp_vol_1y',0)*100:.1f}%")
                st.metric("Max Drawdown", f"{kpis.get('max_drawdown',0)*100:.1f}%")
        summary_text = f"{advice.get('summary','(no summary)')}\n\nAction: {advice.get('one_action','—')}"
        st.session_state.messages.append({"role": "assistant", "content": summary_text})
