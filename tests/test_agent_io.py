import json
import pathlib
import pytest
from jsonschema import ValidationError

from src.agent_io import (
    load_schema,
    validate_sim_request,
    validate_sim_result,
    validate_agent_output,
    make_ok_message,
    make_user_message,
    error_to_string,
)

def test_load_schema_reads_agent_output():
    schema = load_schema("schemas/agent_output.schema.json")
    assert isinstance(schema, dict)
    assert schema.get("title") == "AgentOutput"

def test_validate_sim_request_accepts_minimal_valid():
    # minimal happy-path request expected by your sim
    payload = {"risk_profile": "balanced", "horizon_years": 5, "context": {"demo_seed": 42}}
    validate_sim_request(payload)  # should not raise

def test_validate_sim_request_rejects_invalid_type():
    bad = {"risk_profile": 123, "horizon_years": "five"}
    with pytest.raises(ValidationError):
        validate_sim_request(bad)

def test_make_message_helpers():
    m1 = make_ok_message("hello")
    m2 = make_user_message("hi")
    assert m1["role"] == "assistant" and "hello" in m1["content"]
    assert m2["role"] == "user" and "hi" in m2["content"]

def test_validate_agent_output_happy_path(tmp_path):
    # Build a minimal valid output per updated schema
    out = {
        "status": "ok",
        "run_id": "00000000-0000-0000-0000-000000000000",
        "messages": [make_ok_message("Short advice")],
        "analytics": {"proposed_allocation": {"equities": 0.55, "bonds": 0.4, "cash": 0.05},
                      "kpis": {"exp_return_1y": 0.06, "exp_vol_1y": 0.11, "max_drawdown": 0.17}},
        "allocation": {"equities": 0.55, "bonds": 0.4, "cash": 0.05},
        "kpis": {"exp_return_1y": 0.06, "exp_vol_1y": 0.11, "max_drawdown": 0.17},
        "advice": {"summary": "Concise", "one_action": "Rebalance quarterly.", "disclaimer": "Educational only, not financial advice."},
        "latency_ms": 12.3
    }
    validate_agent_output(out)  # should not raise

def test_error_to_string_validationerror_path():
    from jsonschema import validate
    schema = {"type": "object", "properties": {"x": {"type":"number"}}, "required": ["x"]}
    with pytest.raises(ValidationError) as e:
        validate({"x": "nope"}, schema)
    msg = error_to_string(e.value)
    assert "at $" in msg
