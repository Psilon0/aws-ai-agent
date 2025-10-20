import json
import builtins
import types

from src.lambda_handler import handler

class Ctx:
    aws_request_id = "req-123"

def test_handler_success_path(monkeypatch):
    # Mock Agent.handle to return a minimal valid payload
    def fake_handle(self, body):
        return {
            "status": "ok",
            "run_id": "00000000-0000-0000-0000-000000000000",
            "messages": [{"role": "assistant", "content": "Hi"}],
            "analytics": {},
            "allocation": {"equities": 0.5, "bonds": 0.45, "cash": 0.05},
            "kpis": {"exp_return_1y": 0.05, "exp_vol_1y": 0.1, "max_drawdown": 0.2},
            "advice": {"summary": "Short", "one_action": "Rebalance", "disclaimer": "Educational only, not financial advice."},
            "latency_ms": 1.0
        }
    monkeypatch.setattr("src.agent.Agent.handle", fake_handle)

    event = {"body": json.dumps({"risk_profile": "balanced", "horizon_years": 5, "context": {"demo_seed": 42}}), "headers": {"x-correlation-id": "corr-abc"}}
    resp = handler(event, Ctx())
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["status"] == "ok"
    assert "latency_ms" in body

def test_handler_schema_violation_becomes_error(monkeypatch):
    # Return a payload that violates AgentOutput schema (missing advice)
    def bad_handle(self, body):
        return {"status": "ok", "messages": [{"role": "assistant", "content": "oops"}], "analytics": {}, "latency_ms": 1.0}
    monkeypatch.setattr("src.agent.Agent.handle", bad_handle)

    resp = handler({"body": "{}"}, Ctx())
    body = json.loads(resp["body"])
    assert body["status"] == "error"
    assert any("AgentOutput schema violation" in m["content"] for m in body["messages"])

def test_handler_exception_path(monkeypatch):
    def boom(self, body):
        raise RuntimeError("boom")
    monkeypatch.setattr("src.agent.Agent.handle", boom)

    resp = handler({"body": "{}"}, Ctx())
    body = json.loads(resp["body"])
    assert body["status"] == "error"
    assert any("RuntimeError: boom" in m["content"] for m in body["messages"])
