from __future__ import annotations
import json, time, uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from jsonschema import validate

from src.constants.risk_bands import RISK_BANDS
from src.tools import analytics_stub

TZ = ZoneInfo("Europe/London")

# --- Safe import for risk alerts, with a no-op fallback ---
try:
    from src.tools.risk_alerts import risk_alerts_from_kpis
except Exception:
    def risk_alerts_from_kpis(allocation: dict, kpis: dict):
        return []

def _uuid_v7_like() -> str:
    # Simple readable run id
    return uuid.uuid4().hex[:8] + "-" + datetime.now(TZ).strftime("%Y%m%d%H%M%S")

def _load_schema(path: str) -> dict:
    import pathlib
    p = pathlib.Path("schemas") / path
    with open(p, "r") as f:
        return json.load(f)

# Schemas (must exist in ./schemas/)
SIM_REQ_SCHEMA = _load_schema("sim_request.schema.json")
AGENT_OUT_SCHEMA = _load_schema("agent_output.schema.json")

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def _apply_sentiment_tilt(allocation: dict, risk_band: dict, sentiment: dict | None) -> dict:
    """Tilt equities within band by ±5% scaled by confidence; adjust bonds to keep cash steady."""
    if not sentiment:
        return allocation
    label = sentiment.get("label", "neutral")
    conf = float(sentiment.get("confidence", 0.5))
    tilt_map = {
        "bullish": +0.05,
        "slightly_bullish": +0.025,
        "neutral": 0.0,
        "slightly_bearish": -0.025,
        "bearish": -0.05,
    }
    delta = tilt_map.get(label, 0.0) * conf
    eq = _clamp(allocation["equities"] + delta, risk_band["min_eq"], risk_band["max_eq"])
    # Keep cash constant; give/take from bonds
    cash = allocation["cash"]
    bonds = max(0.0, 1.0 - eq - cash)
    # Round to 3dp and ensure sum=1.000 via cash
    eq = round(eq, 3)
    bonds = round(bonds, 3)
    cash = round(1.0 - round(eq + bonds, 3), 3)
    return {"equities": eq, "bonds": bonds, "cash": cash}

def _local_advice(proposed_alloc: dict, kpis: dict, risk_profile: str) -> dict:
    eq = int(round(proposed_alloc["equities"] * 100))
    bd = int(round(proposed_alloc["bonds"] * 100))
    cs = int(round(proposed_alloc["cash"] * 100))
    er = round(kpis["exp_return_1y"] * 100, 1)
    ev = round(kpis["exp_vol_1y"] * 100, 1)
    summary = (
        f"For a {risk_profile} profile, target ~{eq}% equities, {bd}% bonds, and {cs}% cash. "
        f"Our 1-year simulation implies ~{er}% expected return with ~{ev}% volatility. "
        f"Consider periodic rebalancing to stay within your risk band."
    )
    one_action = "Rebalance to the target mix within the next week."
    disclaimer = "Educational only; not financial advice."
    return {"summary": summary[:1800], "one_action": one_action, "disclaimer": disclaimer}

def run_pipeline(payload: dict) -> dict:
    t0 = time.time()

    # 1) Validate input
    validate(payload, SIM_REQ_SCHEMA)

    rp = payload["risk_profile"].lower()
    bands = RISK_BANDS[rp]

    # 2) Deterministic sim via adapter (calls ProperModel)
    sim = analytics_stub.run_simulation(payload)
    proposed = sim["proposed_allocation"]
    kpis = sim["kpis"]

    # 3) Sentiment tilt within band
    proposed = _apply_sentiment_tilt(proposed, bands, payload.get("sentiment"))

    # 4) Risk alerts (no-op fallback if module missing)
    try:
        alerts = risk_alerts_from_kpis(proposed, kpis)
    except Exception:
        alerts = []

    # 5) Advice (local generator; no Bedrock dependency)
    advice = _local_advice(proposed, kpis, rp)

    # 6) Assemble result
    out = {
        "advice": advice,
        "analytics": {"proposed_allocation": proposed},
        "kpis": kpis,
        "sentiment": payload.get("sentiment") or {"label": "neutral", "confidence": 0.5},
        "risk_alerts": alerts,
        "run_id": _uuid_v7_like(),
        "latency_ms": int((time.time() - t0) * 1000),
    }

    # 7) Validate output
    validate(out, AGENT_OUT_SCHEMA)
    return out

if __name__ == "__main__":
    demo = {"risk_profile": "moderate", "horizon_years": 5, "age": 30, "context": {"demo_seed": 123}}
    print(json.dumps(run_pipeline(demo), indent=2))
