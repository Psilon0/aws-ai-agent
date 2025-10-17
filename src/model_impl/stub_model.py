import math
from src.model_interface.portfolio_model import PortfolioModel
from src.model_interface.types import Profile, MarketState, Bands, ModelOutput
from src.constants.risk_bands import RISK_BANDS
from src.utils.rounding import round_allocation

class StubModel(PortfolioModel):
    def recommend(self, profile: Profile, bands: Bands, market: MarketState, seed: int|None=None) -> ModelOutput:
        base = (bands["min_eq"] + bands["max_eq"]) / 2
        sign = 1 if market["sentiment_label"] == "bullish" else (-1 if market["sentiment_label"] == "bearish" else 0)
        tilt = sign * min(0.05, 0.05 * market["sentiment_confidence"])
        eq = max(bands["min_eq"], min(bands["max_eq"], base + tilt))
        rem = 1 - eq
        bonds = 0.7 * rem
        cash = 0.3 * rem
        alloc = round_allocation({"equities": eq, "bonds": bonds, "cash": cash})
        exp_return = 0.06*alloc["equities"] + 0.03*alloc["bonds"] + 0.02*alloc["cash"]
        vol = 0.18*alloc["equities"] + 0.06*alloc["bonds"]
        mdd = -0.8 * vol
        return {
            "allocation": alloc,
            "kpis": {
                "exp_return_1y": round(exp_return,4),
                "exp_vol_1y": round(vol,4),
                "max_drawdown": round(mdd,4),
            },
            "diagnostics": {"seed": seed, "notes": "stub deterministic model"}
        }
