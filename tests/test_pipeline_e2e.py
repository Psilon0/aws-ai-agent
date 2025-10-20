import json
from src.pipeline import run_pipeline

def test_pipeline_balanced_happy_path(monkeypatch):
    # Disable Bedrock for deterministic local advice
    monkeypatch.setenv("USE_BEDROCK", "0")
    payload = {"risk_profile":"balanced","horizon_years":5,"context":{"demo_seed":42}}
    out = run_pipeline(payload)
    assert out["status"] == "ok"
    assert "analytics" in out and "proposed_allocation" in out["analytics"]
    assert out["allocation"]["equities"] == 0.55
    assert "advice" in out and out["advice"]["summary"]
