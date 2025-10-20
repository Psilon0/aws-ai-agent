import json, pathlib
from jsonschema import validate, ValidationError

def load(p): return json.loads(pathlib.Path(p).read_text())

def test_sim_request_schema_accepts_minimal():
    schema = load("schemas/sim_request.schema.json")
    payload = {"risk_profile":"balanced","horizon_years":5,"context":{"demo_seed":42}}
    validate(payload, schema)

def test_sim_result_schema_accepts_stub_output():
    schema = load("schemas/sim_result.schema.json")
    result = {
        "proposed_allocation":{"equities":0.55,"bonds":0.4,"cash":0.05},
        "kpis":{"exp_return_1y":0.06,"exp_vol_1y":0.11,"max_drawdown":0.17}
    }
    validate(result, schema)
