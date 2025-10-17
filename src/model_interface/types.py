from typing import TypedDict, Literal, Optional

Risk = Literal["conservative","moderate","aggressive"]

class Profile(TypedDict):
    age: int
    risk: Risk
    horizon_years: int

class MarketState(TypedDict):
    sentiment_label: Literal["bullish","neutral","bearish"]
    sentiment_confidence: float
    tz: str
    asof_iso: str

class Bands(TypedDict):
    min_eq: float
    max_eq: float

class Allocation(TypedDict):
    equities: float
    bonds: float
    cash: float

class KPIs(TypedDict, total=False):
    exp_return_1y: float
    exp_vol_1y: float
    max_drawdown: float

class Diagnostics(TypedDict, total=False):
    seed: Optional[int]
    notes: str

class ModelOutput(TypedDict):
    allocation: Allocation
    kpis: KPIs
    diagnostics: Diagnostics
