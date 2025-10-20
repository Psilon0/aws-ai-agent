import json, pathlib
from jsonschema import validate

def test_agent_output_schema_accepts_happy_path():
    schema = json.loads(pathlib.Path("schemas/agent_output.schema.json").read_text())
    sample = {
        "status": "ok",
        "run_id": "123e4567-e89b-12d3-a456-426614174000",
        "messages": [{"role": "assistant", "content": "Short advice text"}],
        "analytics": {"proposed_allocation": {"equities": 0.55, "bonds": 0.4, "cash": 0.05},
                      "kpis": {"exp_return_1y": 0.06, "exp_vol_1y": 0.11, "max_drawdown": 0.17}},
        "allocation": {"equities": 0.55, "bonds": 0.4, "cash": 0.05},
        "kpis": {"exp_return_1y": 0.06, "exp_vol_1y": 0.11, "max_drawdown": 0.17},
        "advice": {"summary": "Concise ≤180 words.", "one_action": "Rebalance quarterly.", "disclaimer": "Educational only, not financial advice."},
        "latency_ms": 123.4
    }
    validate(sample, schema)
