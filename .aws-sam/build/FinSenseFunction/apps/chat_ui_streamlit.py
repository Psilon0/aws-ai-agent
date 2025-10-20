import re
from typing import Dict, Any, List, Optional
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

api_base = st.sidebar.text_input("API Base URL", "http://127.0.0.1:8000")
age = st.sidebar.number_input("Age", min_value=16, max_value=100, value=st.session_state.age_sb, key="age_sb")
risk = st.sidebar.selectbox("Risk Profile", ["conservative", "moderate", "aggressive"], index=1, key="risk_sb")
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
    m_age = re.search(r"(?:^|\D)(1[6-9]|[2-9]\d|100)\s*year(?:s)?\s*old\b", text_l)
    if m_age:
        out["age"] = int(m_age.group(1))
    if re.search(r"\b(high\s*risk|aggressive|growthy|risk[-\s]*seeking)\b", text_l):
        out["risk"] = "aggressive"
    elif re.search(r"\b(moderate|balanced)\b", text_l):
        out["risk"] = "moderate"
    elif re.search(r"\b(low\s*risk|conservative|defensive|safe)\b", text_l):
        out["risk"] = "conservative"
    m_h = re.search(r"\b(1|[2-3]?\d)\s*(?:y|yr|yrs|year|years)\b", text_l)
    if m_h:
        out["horizon_years"] = int(m_h.group(1))
    text_norm = text_l.replace(",", "")
    m_amt = re.search(r"£\s*([0-9]+(?:\.[0-9]{1,2})?)", text_norm) or re.search(r"([0-9]+(?:\.[0-9]{1,2})?)\s*(pounds|gbp)\b", text_norm)
    if not m_amt:
        m_amt = re.search(r"\binvest\s+([0-9]+(?:\.[0-9]{1,2})?)\b", text_norm)
    if m_amt:
        try:
            out["amount_gbp"] = float(m_amt.group(1))
        except Exception:
            pass
    m_pct = re.search(r"(\d{1,2}(?:\.\d+)?)\s*%", text_norm) or re.search(r"(\d{1,2}(?:\.\d+)?)\s*percent", text_norm)
    if m_pct:
        try:
            out["percent_intent"] = float(m_pct.group(1))
        except Exception:
            pass
    return out

# =========================
# Helper: Call API
# =========================
def call_api(message: str) -> Dict[str, Any]:
    payload = {"message": message.strip(), "force_high_vol": bool(force_high_vol)}
    payload["profile"] = {
        "age": int(st.session_state.get("age_sb", 25)),
        "risk": st.session_state.get("risk_sb", "moderate"),
        "horizon_years": int(st.session_state.get("horizon_sb", 5)),
    }
    overrides = parse_overrides(message)
    for key in ("age", "risk", "horizon_years"):
        if key in overrides:
            payload["profile"][key] = overrides[key]
            st.session_state[f"parsed_{key}"] = overrides[key]
    st.session_state["amount_gbp_override"] = overrides.get("amount_gbp")
    st.session_state["percent_intent"] = overrides.get("percent_intent")
    if demo_seed.strip():
        try:
            payload["demo_seed"] = int(demo_seed.strip())
        except ValueError:
            pass
    r = requests.post(f"{api_base.rstrip('/')}/chat", json=payload, timeout=12)
    r.raise_for_status()
    return payload, r.json()

# =========================
# Helper: Display
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

def alert_box(a: Dict[str, Any]):
    sev = (a.get("severity", "low") or "").lower()
    text = f"**{a.get('type','alert')}**\n{a.get('evidence','')}\n**Action:** {a.get('suggested_action','')}"
    if sev == "high":
        st.error(text)
    elif sev == "medium":
        st.warning(text)
    else:
        st.info(text)

# =========================
# Chat UI
# =========================
st.title("Portfolio Recommendation Agent")
st.caption("Example: “I am 25, moderate risk, 5-year horizon.”")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Type your message")
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
        band = (data.get("allocation_meta") or {}).get("band", {})
        alerts = data.get("risk_alerts", [])
        meta = {
            "run_id": data.get("run_id", ""),
            "latency_ms": data.get("latency_ms", 0),
            "version": data.get("version", "")
        }

        with st.chat_message("assistant"):
            risk_used = (data.get("advice") or {}).get("summary", "").split("your ", 1)[-1].split(" risk band", 1)[0] if (data.get("advice") or {}).get("summary") else "—"
            st.caption(f"Risk: {risk_used} | Band: {int(band.get('min_eq', 0)*100)}–{int(band.get('max_eq', 0)*100)}% equities")
            st.markdown("**Recommendation Summary**")
            st.write(advice.get("summary", "No summary available."))
            st.markdown(f"**Action:** {advice.get('one_action', '')}")
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

            if alerts:
                st.markdown("### Risk Alerts")
                for a in alerts:
                    alert_box(a)
            st.caption(f"Run ID: `{meta['run_id']}` | {meta['latency_ms']} ms | v{meta['version']}")

        summary_text = f"{advice.get('summary','(no summary)')}\n\nAction: {advice.get('one_action','—')}"
        st.session_state.messages.append({"role": "assistant", "content": summary_text})
