# PURPOSE: Generate risk or sentiment alerts based on model KPIs and market sentiment.
# CONTEXT: Called by backend to flag high volatility or sentiment changes.
# CREDITS: Original work — no external code reuse.

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os, json

TZ = ZoneInfo("Europe/London")

@dataclass
class Alert:
    """
    Represents a single portfolio alert.

    attributes:
    - type: str – short identifier (e.g. 'vol_spike' or 'sentiment_flip').
    - severity: str – qualitative impact ('low', 'medium', 'high').
    - evidence: str – short text describing why the alert was raised.
    - suggested_action: str – simple guidance for the user.
    """
    type: str
    severity: str
    evidence: str
    suggested_action: str

def _yesterday_sentiment() -> dict | None:
    """
    Load yesterday’s sentiment JSON file if it exists.

    returns:
    - dict or None – the sentiment record or None if unavailable/corrupted.
    """
    y = (datetime.now(TZ) - timedelta(days=1)).strftime("%Y-%m-%d")
    p = os.path.join("runs", "sentiment", f"{y}_Europe-London.json")
    if os.path.exists(p):
        try:
            with open(p) as fh:
                return json.load(fh)
        except Exception:
            return None
    return None

def calc_alerts(kpis: Dict[str, float], today_sentiment: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluate current KPIs and sentiment to generate alerts.

    parameters:
    - kpis: dict – {"exp_vol_1y": float, ...}, model output metrics.
    - today_sentiment: dict – {"label": str, "confidence": float, ...}.

    returns:
    - list[dict] – alert objects converted to plain dictionaries.
    """
    alerts: list[Alert] = []

    # ---- Volatility rule ----
    # Raise a warning if annualised volatility exceeds thresholds.
    vol = float(kpis.get("exp_vol_1y", 0.0))
    if vol >= 0.18:
        alerts.append(
            Alert(
                "vol_spike",
                "high",
                f"Annualised vol≈{vol:.2f} ≥ 0.18",
                "Consider raising bonds/cash and shortening duration"
            )
        )
    elif vol >= 0.12:
        alerts.append(
            Alert(
                "vol_spike",
                "medium",
                f"Annualised vol≈{vol:.2f} ≥ 0.12",
                "Trim equities within your band"
            )
        )

    # ---- Sentiment flip rule ----
    # If sentiment label changed since yesterday, note it.
    y = _yesterday_sentiment()
    if (
        y
        and y.get("label")
        and today_sentiment.get("label")
        and y["label"] != today_sentiment["label"]
    ):
        alerts.append(
            Alert(
                "sentiment_flip",
                "medium",
                f"Sentiment {y['label']} → {today_sentiment['label']}",
                "Rebalance to target and review stops"
            )
        )

    # Return plain dicts so they serialize easily into JSON.
    return [a.__dict__ for a in alerts]
