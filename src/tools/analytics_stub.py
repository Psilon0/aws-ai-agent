from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo

from src.model_impl.proper_model import ProperModel
from src.constants.risk_bands import RISK_BANDS

TZ = ZoneInfo("Europe/London")
_model = ProperModel()

def run_simulation(payload):
    rp = (payload.get("risk_profile") or "moderate").lower()
    horizon = int(payload.get("horizon_years") or 5)
    ctx = payload.get("context") or {}
    seed = ctx.get("demo_seed")

    profile = {
        "age": int(payload.get("age") or 35),
        "risk": rp,
        "horizon_years": horizon,
    }
    bands = RISK_BANDS[rp]
    market = {
        "sentiment_label": (payload.get("sentiment") or {}).get("label", "neutral"),
        "sentiment_confidence": (payload.get("sentiment") or {}).get("confidence", 0.5),
        "tz": str(TZ),
        "asof_iso": datetime.now(TZ).isoformat(timespec="seconds"),
    }

    out = _model.recommend(profile, bands, market, seed=seed)
    return {
        "proposed_allocation": out["allocation"],
        "kpis": out["kpis"],
    }
