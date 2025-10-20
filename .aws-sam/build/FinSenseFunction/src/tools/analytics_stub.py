from __future__ import annotations
import random

def run_simulation(payload):
    """
    Deterministic simulator for FinSense.
    Inputs: payload = {"risk_profile": str, "horizon_years": int, "context": {"demo_seed": int}}
    Output:
      {
        "proposed_allocation": {"equities": float, "bonds": float, "cash": float},
        "kpis": {"exp_return_1y": float, "exp_vol_1y": float, "max_drawdown": float}
      }
    """
    ctx = (payload.get("context") or {})
    seed = ctx.get("demo_seed", 42)
    random.seed(seed)

    rp = (payload.get("risk_profile") or "balanced").lower()
    base = {
        "conservative": (0.04, 0.07, 0.12),
        "balanced":     (0.06, 0.11, 0.17),
        "aggressive":   (0.08, 0.16, 0.25),
    }.get(rp, (0.06, 0.11, 0.17))

    # Tiny jitter for realism but deterministic per seed
    jitter = (random.random() - 0.5) * 0.01
    exp_ret, vol, mdd = base[0] + jitter, base[1] + jitter, base[2] + jitter

    allocs = {
        "conservative": {"equities": 0.35, "bonds": 0.60, "cash": 0.05},
        "balanced":     {"equities": 0.55, "bonds": 0.40, "cash": 0.05},
        "aggressive":   {"equities": 0.75, "bonds": 0.20, "cash": 0.05},
    }.get(rp, {"equities": 0.55, "bonds": 0.40, "cash": 0.05})

    return {
        "proposed_allocation": allocs,
        "kpis": {
            "exp_return_1y": round(exp_ret, 4),
            "exp_vol_1y": round(vol, 4),
            "max_drawdown": round(mdd, 4),
        }
    }
