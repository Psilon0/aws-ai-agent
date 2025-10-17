from __future__ import annotations

import os
import json
import time
import uuid
import hashlib
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from src.constants.risk_bands import RISK_BANDS
from src.model_impl.stub_model import StubModel
from src.tools.risk_alerts import calc_alerts

APP_VERSION = "0.1.0"
TZ = "Europe/London"
tz = ZoneInfo(TZ)
_app_start = time.time()

app = FastAPI(
    title="aws-ai-agent local API",
    version=APP_VERSION
)

# -----------------------------
# Pydantic models (I/O schema)
# -----------------------------
class ProfileIn(BaseModel):
    age: Optional[int] = Field(None, ge=16, le=100)
    risk: Optional[str] = Field(None)
    horizon_years: Optional[int] = Field(None, ge=1, le=40)

class ChatIn(BaseModel):
    message: str = Field(..., min_length=1)
    profile: Optional[ProfileIn] = None
    demo_seed: Optional[int] = None
    force_high_vol: Optional[bool] = False

class AdviceOut(BaseModel):
    summary: str
    one_action: str
    disclaimer: str

class AdvancedPayload(BaseModel):
    seed: Optional[int] = None
    defaults_used: bool = False
    prompt_sha256: str
    llm_timed_out: bool = False

class ChatOut(BaseModel):
    version: str
    run_id: str
    latency_ms: int
    advice: AdviceOut
    allocation: Dict[str, float]
    allocation_meta: Dict[str, Any]
    kpis: Dict[str, float]
    sentiment: Dict[str, Any]
    risk_alerts: List[Dict[str, Any]]
    advanced_payload: AdvancedPayload

# -----------------------------
# Helpers
# -----------------------------
def hash_prompt(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

def parse_overrides(text: str) -> dict:
    """
    Extract age, risk, horizon from free text like:
      "55 years old", "high/aggressive", "low/conservative/safe/defensive", "14 years", "5y"
    """
    text_l = (text or "").lower()
    out: Dict[str, Any] = {}

    m_age = re.search(r'(?:^|\D)(1[6-9]|[2-9]\d|100)\s*year(?:s)?\s*old\b', text_l)
    if m_age:
        out["age"] = int(m_age.group(1))

    if re.search(r'\b(high\s*risk|aggressive)\b', text_l):
        out["risk"] = "aggressive"
    elif re.search(r'\b(moderate|balanced)\b', text_l):
        out["risk"] = "moderate"
    elif re.search(r'\b(low\s*risk|conservative|defensive|safe)\b', text_l):
        out["risk"] = "conservative"

    m_h = re.search(r'\b(1|[2-3]?\d)\s*(?:y|yr|yrs|year|years)\b', text_l)
    if m_h:
        out["horizon_years"] = int(m_h.group(1))

    return out

class SafeProfile(BaseModel):
    age: int
    risk: str
    horizon_years: int

def safe_defaults(p_like: Any) -> SafeProfile:
    """Apply defaults + clamp + normalize risk names."""
    age = getattr(p_like, "age", None)
    risk = getattr(p_like, "risk", None)
    horizon_years = getattr(p_like, "horizon_years", None)

    # Accept dict-like too
    if isinstance(p_like, dict):
        age = p_like.get("age", age)
        risk = p_like.get("risk", risk)
        horizon_years = p_like.get("horizon_years", horizon_years)

    # Defaults
    if age is None: age = 30
    if horizon_years is None: horizon_years = 5
    # Normalize risk
    if risk is None or risk == "balanced": risk = "moderate"
    risk = str(risk).lower()
    if risk not in {"conservative","moderate","aggressive"}:
        risk = "moderate"

    # Clamp
    age = max(16, min(100, int(age)))
    horizon_years = max(1, min(40, int(horizon_years)))

    return SafeProfile(age=age, risk=risk, horizon_years=horizon_years)

def load_sentiment_today() -> Dict[str, Any]:
    today = datetime.now(tz).strftime("%Y-%m-%d")
    path = os.path.join("runs","sentiment", f"{today}_Europe-London.json")
    if os.path.exists(path):
        try:
            with open(path) as fh:
                s = json.load(fh)
            return {
                "label": s.get("label", "neutral"),
                "confidence": float(s.get("confidence", 0.55)),
                "asof_iso": s.get("asof_iso", datetime.now(tz).isoformat(timespec="seconds")),
            }
        except Exception:
            pass
    # fallback neutral
    return {"label":"neutral","confidence":0.55,"asof_iso": datetime.now(tz).isoformat(timespec="seconds")}

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/health")
def health():
    today = datetime.now(tz).strftime("%Y-%m-%d")
    has_sent = os.path.exists(os.path.join("runs","sentiment", f"{today}_Europe-London.json"))
    return {
        "status":"ok",
        "version": APP_VERSION,
        "uptime_s": int(time.time() - _app_start),
        "tz": TZ,
        "has_today_sentiment": bool(has_sent),
    }

@app.post("/chat")
def chat(body: ChatIn) -> ChatOut:
    t0 = time.time()
    run_id = uuid.uuid4().hex

    # Merge message-derived overrides with explicit profile, then apply defaults
    overrides = parse_overrides(body.message)
    prof_in = body.profile.dict() if body.profile else {}
    merged = {
        "age": prof_in.get("age"),
        "risk": prof_in.get("risk"),
        "horizon_years": prof_in.get("horizon_years"),
    }
    merged.update({k:v for k,v in overrides.items() if k in {"age","risk","horizon_years"}})
    profile = safe_defaults(merged)

    # Sentiment (timezone-aware cache)
    sentiment = load_sentiment_today()

    # Risk band
    band = RISK_BANDS[profile.risk]

    # Market payload for model
    market = {
        "sentiment_label": sentiment["label"],
        "sentiment_confidence": sentiment["confidence"],
        "tz": TZ,
        "asof_iso": sentiment["asof_iso"],
    }

    # Call model
    model = StubModel()
    out = model.recommend(
        {"age": profile.age, "risk": profile.risk, "horizon_years": profile.horizon_years},
        band,
        market,
        seed=body.demo_seed
    )

    # Validate allocation
    alloc_in = out.get("allocation") or {}
    for k in ("equities","bonds","cash"):
        if k not in alloc_in:
            raise HTTPException(status_code=400, detail=f"model allocation missing key: {k}")
    allocation = {k: float(alloc_in[k]) for k in ("equities","bonds","cash")}

    # KPIs
    k_in = out.get("kpis") or {}
    kpis = {
        "exp_return_1y": float(k_in.get("exp_return_1y", 0.0)),
        "exp_vol_1y": float(k_in.get("exp_vol_1y", 0.0)),
        "max_drawdown": float(k_in.get("max_drawdown", 0.0)),
    }

    # Alerts
    force_high = bool(body.force_high_vol)
    try:
        risk_alerts = calc_alerts(kpis, sentiment, force_high_vol=force_high)
    except TypeError:
        risk_alerts = calc_alerts(kpis, sentiment)

    # Advice text (concise, professional)
    summary = (
        f"Given {sentiment['label']} sentiment ({sentiment['confidence']:.2f}) "
        f"and your {profile.risk} risk band, the portfolio holds "
        f"{allocation['equities']*100:.1f}% equities to balance return vs. risk."
    )
    one_action = "Rebalance to target mix and set a 12-month check-in."
    disclaimer = "Educational only, not financial advice."

    latency_ms = int((time.time() - t0) * 1000)

    resp = ChatOut(
        version=APP_VERSION,
        run_id=run_id,
        latency_ms=latency_ms,
        advice=AdviceOut(summary=summary, one_action=one_action, disclaimer=disclaimer),
        allocation=allocation,
        allocation_meta={"band": {"min_eq": band["min_eq"], "max_eq": band["max_eq"]}},
        kpis=kpis,
        sentiment=sentiment,
        risk_alerts=risk_alerts,
        advanced_payload=AdvancedPayload(
            seed=body.demo_seed,
            defaults_used=(body.profile is None),
            prompt_sha256=hash_prompt(body.message),
            llm_timed_out=False,
        ),
    )

    # Persist output for demo
    if not os.getenv("DO_NOT_STORE_CHATS"):
        os.makedirs("runs/outputs", exist_ok=True)
        with open(os.path.join("runs","outputs", f"{run_id}.json"), "w") as fh:
            json.dump(jsonable_encoder(resp), fh, indent=2)

    return resp
