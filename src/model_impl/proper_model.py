# PURPOSE: “Proper” portfolio model that proposes an allocation and KPIs.
# CONTEXT: Uses a lifecycle equity/bond mix adjusted by sentiment and horizon,
#          then derives expected return/vol via a simple one-step Monte Carlo.
# CREDITS: Original work — no external code reuse.
# NOTE: Behaviour unchanged; comments/docstrings only.

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple
import math
import numpy as np
from zoneinfo import ZoneInfo
from datetime import datetime

from src.model_interface.portfolio_model import PortfolioModel
from src.model_interface.types import Profile, MarketState, Bands, ModelOutput
from src.constants.risk_bands import RISK_BANDS
from src.utils.rounding import round_allocation

TZ = ZoneInfo("Europe/London")

# Capital market assumptions (annualised). Tuned constants for the demo engine.
ANNUAL_RETURN_EQ   = 0.0889
ANNUAL_VOL_EQ      = 0.1526
ANNUAL_RETURN_BOND = 0.0292
ANNUAL_VOL_BOND    = 0.0738
EQ_BOND_RHO        = -0.0322   # low/negative correlation between equities and bonds
BANK_MU            = 0.0282    # not directly used here, kept for completeness/future
BANK_SIGMA         = 0.0001    # (same as above)

# Lifecycle targets (equity, bond) before sentiment/horizon adjustments.
OPT_AGGR = (1.0,   0.0)
OPT_MOD  = (0.459, 0.541)
OPT_MID  = (0.4202, 0.5798)

def _mix_mu_sigma(eq_w: float, bd_w: float) -> Tuple[float, float]:
    """
    Mix expected return/vol for a 2-asset portfolio (equities + bonds).

    parameters:
    - eq_w: float – equity weight
    - bd_w: float – bond weight

    returns:
    - (mu, sigma): tuple[float, float] – annualised expected return and volatility
    """
    mu = eq_w*ANNUAL_RETURN_EQ + bd_w*ANNUAL_RETURN_BOND
    var = (eq_w*ANNUAL_VOL_EQ)**2 + (bd_w*ANNUAL_VOL_BOND)**2 \
          + 2*EQ_BOND_RHO*eq_w*bd_w*ANNUAL_VOL_EQ*ANNUAL_VOL_BOND
    return mu, math.sqrt(max(var, 0.0))

def _lifecycle_mix(age: int) -> Tuple[float, float]:
    """
    Coarse lifecycle rule of thumb for baseline equity/bond split.

    returns:
    - (eq, bd): tuple[float, float] – target equity and bond weights before tweaks
    """
    if age < 45:
        return OPT_AGGR
    elif age < 55:
        return OPT_MOD
    return OPT_MID

def _clamp(x: float, lo: float, hi: float) -> float:
    """Clamp x to the [lo, hi] interval."""
    return min(hi, max(lo, x))

@dataclass
class MCConfig:
    """
    Monte Carlo settings.

    attributes:
    - n_paths: int – number of scenarios for the 1-year return draw
    - horizon_years: int – unused in the one-step MC but kept for parity
    - dt: float – time step in years (1.0 = 1 year)
    """
    n_paths: int = 3000
    horizon_years: int = 1
    dt: float = 1.0

class ProperModel(PortfolioModel):
    """
    Portfolio model:
    1) Start from lifecycle equity/bond weights based on age.
    2) Apply a small sentiment tilt (±3% × confidence), clamped to risk band.
    3) Allocate the residual between bonds and cash using a simple horizon rule.
    4) Round allocation and compute KPIs via a one-step lognormal MC.
    """

    def __init__(self, mc: MCConfig | None = None):
        self.mc = mc or MCConfig()

    def recommend(self, profile: Profile, bands: Bands, market: MarketState, seed: int | None = None) -> ModelOutput:
        """
        Produce an allocation and KPIs for the given profile and market state.

        parameters:
        - profile: Profile – expects keys {age, horizon_years}
        - bands: Bands – risk band constraints with min_eq / max_eq
        - market: MarketState – may include sentiment_label and sentiment_confidence
        - seed: int|None – RNG seed for reproducible KPIs

        returns:
        - ModelOutput – {"allocation": {...}, "kpis": {...}, "diagnostics": {...}}
        """
        age = int(profile.get("age") or 35)
        horizon = int(profile.get("horizon_years") or 5)

        # Baseline lifecycle equity/bond mix by age.
        lc_eq, lc_bd = _lifecycle_mix(age)
        eq_target = lc_eq

        # Sentiment tilt (small, confidence-weighted), then clamp to band.
        sent = (market or {}).get("sentiment_label", "neutral")
        conf = float((market or {}).get("sentiment_confidence", 0.5) or 0.5)
        tilt_map = {"bullish": 0.03, "neutral": 0.0, "bearish": -0.03}
        eq_target = eq_target + tilt_map.get(sent, 0.0) * conf
        eq = _clamp(eq_target, bands["min_eq"], bands["max_eq"])

        # Split the residual between bonds and cash based on horizon.
        residual = 1.0 - eq
        if horizon <= 3:
            bonds_share = 0.65
        elif horizon <= 7:
            bonds_share = 0.80
        else:
            bonds_share = 0.85
        bd = residual * bonds_share
        cash = residual - bd

        # Round and enforce sum=1.0 via cash residual.
        alloc = round_allocation({"equities": eq, "bonds": bd, "cash": cash})

        # Convert allocation to portfolio mu/sigma using the EPQ mix assumptions.
        mu_mix, sig_mix = _mix_mu_sigma(alloc["equities"], alloc["bonds"])

        # KPI estimates via one-step lognormal draw (geometric Brownian assumption).
        rng = np.random.default_rng(seed if seed is not None else 42)
        exp_ret_1y, exp_vol_1y, max_dd = self._mc_kpis(mu_mix, sig_mix, rng)

        return {
            "allocation": alloc,
            "kpis": {
                "exp_return_1y": round(float(exp_ret_1y), 4),
                "exp_vol_1y": round(float(exp_vol_1y), 4),
                "max_drawdown": round(float(max_dd), 4),
            },
            "diagnostics": {
                "age": age,
                "horizon_years": horizon,
                "mu_port": round(mu_mix, 5),
                "sigma_port": round(sig_mix, 5),
                "sentiment": sent,
                "sent_conf": conf,
                "asof_iso": datetime.now(TZ).isoformat(timespec="seconds"),
                "engine": "EPQ-mix+MC",
            },
        }

    def _mc_kpis(self, mu: float, sigma: float, rng: np.random.Generator) -> Tuple[float, float, float]:
        """
        One-step Monte Carlo (lognormal) to estimate return, vol, and a proxy drawdown.

        parameters:
        - mu: float – annualised expected return of the mix
        - sigma: float – annualised volatility of the mix
        - rng: np.random.Generator – pre-seeded RNG for reproducibility

        returns:
        - (exp_return_1y, exp_vol_1y, max_drawdown): tuple[float, float, float]
        """
        n = self.mc.n_paths
        dt = self.mc.dt
        z = rng.standard_normal(n)
        logR = (mu - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * z
        R = np.exp(logR) - 1.0
        exp_return_1y = float(np.mean(R))
        exp_vol_1y = float(np.std(R, ddof=1))
        max_drawdown = -0.8 * exp_vol_1y  # simple proxy relating drawdown to volatility
        return exp_return_1y, exp_vol_1y, max_drawdown
