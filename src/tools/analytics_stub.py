# PURPOSE: Simple deterministic simulator for FinSense portfolio analytics.
# CONTEXT: Acts as a lightweight backend model that generates example outputs
#          for allocation and key performance indicators (KPIs).
# CREDITS: Original work — no external code reuse.
# NOTE: Functionality is unchanged; only comments/docstrings have been added.

from __future__ import annotations
import random

def run_simulation(payload):
    """
    Deterministic simulator for FinSense portfolio analytics.

    parameters:
    - payload: dict
        Expected keys:
        {
          "risk_profile": str,              # one of {"conservative","balanced","aggressive"}
          "horizon_years": int,             # investment horizon, currently unused
          "context": {"demo_seed": int}     # fixed seed for repeatable demo output
        }

    returns:
    - dict:
        {
          "proposed_allocation": {"equities": float, "bonds": float, "cash": float},
          "kpis": {
              "exp_return_1y": float,      # expected 1-year return
              "exp_vol_1y": float,         # expected volatility (annualised)
              "max_drawdown": float        # simulated maximum drawdown
          }
        }

    notes:
    - This stub is deterministic for repeatable demo/testing purposes.
    - It introduces a tiny “jitter” based on the random seed to avoid perfectly identical numbers.
    - Horizon value is included for compatibility but not yet used in the calculation.
    """
    # Pull seed from context; default to 42 for reproducible demos.
    ctx = (payload.get("context") or {})
    seed = ctx.get("demo_seed", 42)
    random.seed(seed)

    # Risk profile determines baseline expected return, volatility, and drawdown.
    # Each tuple = (expected return, volatility, max drawdown).
    rp = (payload.get("risk_profile") or "balanced").lower()
    base = {
        "conservative": (0.04, 0.07, 0.12),
        "balanced":     (0.06, 0.11, 0.17),
        "aggressive":   (0.08, 0.16, 0.25),
    }.get(rp, (0.06, 0.11, 0.17))

    # Add a tiny deterministic jitter to make repeated runs feel more “real”.
    # random.random() ∈ [0,1), so this keeps jitter roughly between -0.005 and +0.005.
    jitter = (random.random() - 0.5) * 0.01
    exp_ret, vol, mdd = base[0] + jitter, base[1] + jitter, base[2] + jitter

    # Static allocations per risk profile; conservative = bond-heavy, aggressive = equity-heavy.
    allocs = {
        "conservative": {"equities": 0.35, "bonds": 0.60, "cash": 0.05},
        "balanced":     {"equities": 0.55, "bonds": 0.40, "cash": 0.05},
        "aggressive":   {"equities": 0.75, "bonds": 0.20, "cash": 0.05},
    }.get(rp, {"equities": 0.55, "bonds": 0.40, "cash": 0.05})

    # Return both allocation and KPIs, rounded to 4 decimals for readability.
    return {
        "proposed_allocation": allocs,
        "kpis": {
            "exp_return_1y": round(exp_ret, 4),
            "exp_vol_1y": round(vol, 4),
            "max_drawdown": round(mdd, 4),
        }
    }
