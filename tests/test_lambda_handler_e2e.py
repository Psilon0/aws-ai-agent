import json, os
from src.lambda_handler import handler

class Ctx: aws_request_id = "req-xyz"

def test_handler_pipeline_ok(monkeypatch):
    monkeypatch.setenv("USE_BEDROCK", "0")  # ensure no external calls
    body = {"risk_profile":"balanced","horizon_years":5,"context":{"demo_seed":42}}
    evt = {"body": json.dumps(body), "headers": {"x-correlation-id":"corr-1"}}
    resp = handler(evt, Ctx())
    assert resp["statusCode"] == 200
    data = json.loads(resp["body"])
    assert data["status"] == "ok"
    assert "allocation" in data and "kpis" in data and "advice" in data
