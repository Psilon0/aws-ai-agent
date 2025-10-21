def risk_alerts_from_kpis(allocation: dict, kpis: dict):
    alerts = []
    vol = float(kpis.get("exp_vol_1y", 0))
    eq = float(allocation.get("equities", 0))
    if vol >= 0.18:
        alerts.append({"type":"volatility","severity":"high",
                       "evidence":f"Expected vol {vol:.1%} exceeds 18%",
                       "suggested_action":"Reduce equity or add bonds/cash."})
    elif vol >= 0.12:
        alerts.append({"type":"volatility","severity":"medium",
                       "evidence":f"Expected vol {vol:.1%} exceeds 12%",
                       "suggested_action":"Review risk tolerance; consider small rebalance."})
    if eq > 0.70:
        alerts.append({"type":"equity_concentration","severity":"medium",
                       "evidence":f"Equities at {eq:.0%} of portfolio",
                       "suggested_action":"Trim equities towards target band."})
    return alerts
