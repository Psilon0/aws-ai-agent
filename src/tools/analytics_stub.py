"""
Temporary stub for the portfolio simulator.
Replace `run_simulation(request: dict)` with your real implementation later.
"""
from typing import Dict, Any

def run_simulation(request: Dict[str, Any]) -> Dict[str, Any]:
    risk = (request.get("risk_profile") or "balanced").lower()
    presets = {
        "conservative": {"equities": 0.35, "bonds": 0.55, "cash": 0.10},
        "balanced":     {"equities": 0.55, "bonds": 0.40, "cash": 0.05},
        "aggressive":   {"equities": 0.75, "bonds": 0.20, "cash": 0.05},
    }
    alloc = presets.get(risk, presets["balanced"])
    # KPI placeholders—swap when your simulator is ready
    kpis = {"exp_return_1y": 0.06, "exp_vol_1y": 0.11, "max_drawdown": 0.17}
    return {"proposed_allocation": alloc, "kpis": kpis, "meta": {"source": "stub"}}
