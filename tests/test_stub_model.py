from src.model_impl.stub_model import StubModel
from src.constants.risk_bands import RISK_BANDS

def test_stub_allocation_sum_and_band():
    m = StubModel()
    band = RISK_BANDS["moderate"]
    market = {"sentiment_label":"bearish","sentiment_confidence":0.9,"tz":"Europe/London","asof_iso":"2025-10-17T00:00:00"}
    prof = {"age":30,"risk":"moderate","horizon_years":5}
    out = m.recommend(prof, band, market)
    alloc = out["allocation"]
    s = round(sum(alloc.values()),3)
    assert abs(s-1.0) < 1e-6
    assert band["min_eq"] <= alloc["equities"] <= band["max_eq"]
