from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os, json

TZ = ZoneInfo("Europe/London")

@dataclass
class Alert:
    type: str
    severity: str
    evidence: str
    suggested_action: str

def _yesterday_sentiment() -> dict|None:
    y = (datetime.now(TZ) - timedelta(days=1)).strftime("%Y-%m-%d")
    p = os.path.join("runs","sentiment", f"{y}_Europe-London.json")
    if os.path.exists(p):
        try:
            with open(p) as fh: return json.load(fh)
        except Exception: return None
    return None

def calc_alerts(kpis: Dict[str,float], today_sentiment: Dict[str,Any]) -> List[Dict[str,Any]]:
    alerts: list[Alert] = []

    # vol_spike: simple rule-of-thumb on annual vol
    vol = float(kpis.get("exp_vol_1y", 0.0))
    if vol >= 0.18:
        alerts.append(Alert("vol_spike","high",f"Annualised vol≈{vol:.2f} ≥ 0.18","Consider raising bonds/cash and shortening duration"))
    elif vol >= 0.12:
        alerts.append(Alert("vol_spike","medium",f"Annualised vol≈{vol:.2f} ≥ 0.12","Trim equities within your band"))

    # sentiment_flip: compare to yesterday cache if present
    y = _yesterday_sentiment()
    if y and y.get("label") and today_sentiment.get("label") and y["label"] != today_sentiment["label"]:
        alerts.append(Alert("sentiment_flip","medium",f"Sentiment {y['label']} → {today_sentiment['label']}","Rebalance to target and review stops"))

    return [a.__dict__ for a in alerts]
