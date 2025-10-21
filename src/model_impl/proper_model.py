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

ANNUAL_RETURN_EQ   = 0.0889
ANNUAL_VOL_EQ      = 0.1526
ANNUAL_RETURN_BOND = 0.0292
ANNUAL_VOL_BOND    = 0.0738
EQ_BOND_RHO        = -0.0322
BANK_MU            = 0.0282
BANK_SIGMA         = 0.0001

OPT_AGGR = (1.0,   0.0)
OPT_MOD  = (0.459, 0.541)
OPT_MID  = (0.4202, 0.5798)

def _mix_mu_sigma(eq_w: float, bd_w: float) -> Tuple[float, float]:
    mu = eq_w*ANNUAL_RETURN_EQ + bd_w*ANNUAL_RETURN_BOND
    var = (eq_w*ANNUAL_VOL_EQ)**2 + (bd_w*ANNUAL_VOL_BOND)**2 \
          + 2*EQ_BOND_RHO*eq_w*bd_w*ANNUAL_VOL_EQ*ANNUAL_VOL_BOND
    return mu, math.sqrt(max(var, 0.0))

def _lifecycle_mix(age: int) -> Tuple[float, float]:
    if age < 45:
        return OPT_AGGR
    elif age < 55:
        return OPT_MOD
    return OPT_MID

def _clamp(x: float, lo: float, hi: float) -> float:
    return min(hi, max(lo, x))

@dataclass
class MCConfig:
    n_paths: int = 3000
    horizon_years: int = 1
    dt: float = 1.0

class ProperModel(PortfolioModel):
    def __init__(self, mc: MCConfig | None = None):
        self.mc = mc or MCConfig()

    def recommend(self, profile: Profile, bands: Bands, market: MarketState, seed: int | None = None) -> ModelOutput:
        age = int(profile.get("age") or 35)
        horizon = int(profile.get("horizon_years") or 5)

        lc_eq, lc_bd = _lifecycle_mix(age)
        eq_target = lc_eq
        sent = (market or {}).get("sentiment_label", "neutral")
        conf = float((market or {}).get("sentiment_confidence", 0.5) or 0.5)
        tilt_map = {"bullish": 0.03, "neutral": 0.0, "bearish": -0.03}
        eq_target = eq_target + tilt_map.get(sent, 0.0) * conf
        eq = _clamp(eq_target, bands["min_eq"], bands["max_eq"])

        residual = 1.0 - eq
        if horizon <= 3:
            bonds_share = 0.65
        elif horizon <= 7:
            bonds_share = 0.80
        else:
            bonds_share = 0.85
        bd = residual * bonds_share
        cash = residual - bd

        alloc = round_allocation({"equities": eq, "bonds": bd, "cash": cash})

        mu_mix, sig_mix = _mix_mu_sigma(alloc["equities"], alloc["bonds"])
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
        n = self.mc.n_paths
        dt = self.mc.dt
        z = rng.standard_normal(n)
        logR = (mu - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * z
        R = np.exp(logR) - 1.0
        exp_return_1y = float(np.mean(R))
        exp_vol_1y = float(np.std(R, ddof=1))
        max_drawdown = -0.8 * exp_vol_1y
        return exp_return_1y, exp_vol_1y, max_drawdown
