from typing import Dict, Any, List
import os, json
import boto3
from jsonschema import validate as json_validate, ValidationError

from src.tools.analytics_stub import run_simulation

with open(os.path.join(os.path.dirname(__file__), "prompts", "sim_request_prompt.md"), "r", encoding="utf-8") as f:
    SIM_PROMPT = f.read()
with open(os.path.join(os.path.dirname(__file__), "prompts", "final_explainer_prompt.md"), "r", encoding="utf-8") as f:
    EXPLAIN_PROMPT = f.read()

with open(os.path.join(os.path.dirname(__file__), "..", "schemas", "sim_request.schema.json"), "r", encoding="utf-8") as f:
    SIM_REQ_SCHEMA = json.load(f)
with open(os.path.join(os.path.dirname(__file__), "..", "schemas", "sim_result.schema.json"), "r", encoding="utf-8") as f:
    SIM_RES_SCHEMA = json.load(f)

REGION = os.getenv("AWS_REGION", "eu-west-2")
MODEL_ID = os.getenv("MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")
br = boto3.client("bedrock-runtime", region_name=REGION)

def _invoke_llm(messages: List[Dict[str, str]]) -> str:
    body = {"messages": messages}
    resp = br.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
    raw = resp.get("body")
    return raw if isinstance(raw, str) else json.dumps(raw)

def _make_sim_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = (payload.get("message") or {}).get("text", "")
    ctx  = payload.get("context") or {}
    hints = {
        "risk_profile": ctx.get("risk_profile", "balanced"),
        "horizon_years": int(ctx.get("horizon_years", 5))
    }
    messages = [
        {"role": "system", "content": SIM_PROMPT},
        {"role": "user", "content": json.dumps({"message": text, "hints": hints})}
    ]
    out = _invoke_llm(messages)
    try:
        sim_req = json.loads(out)
        json_validate(sim_req, SIM_REQ_SCHEMA)
        return sim_req
    except Exception:
        # Fallback to hints if model didn't return strict JSON
        return hints

def _explain_result(sim_req: Dict[str, Any], sim_res: Dict[str, Any]) -> str:
    messages = [
        {"role": "system", "content": EXPLAIN_PROMPT},
        {"role": "user", "content": json.dumps({"request": sim_req, "result": sim_res})}
    ]
    return _invoke_llm(messages)

def run_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    # 1) Plan a SimRequest via Bedrock
    sim_req = _make_sim_request(payload)

    # 2) Call simulator (stub for now)
    sim_res = run_simulation(sim_req)
    try:
        json_validate(sim_res, SIM_RES_SCHEMA)
    except ValidationError as e:
        raise RuntimeError(f"Simulator result failed schema: {e.message}")

    # 3) Explain via Bedrock
    explanation = _explain_result(sim_req, sim_res)

    # 4) Wrap in AgentOutput contract
    return {
        "status": "ok",
        "messages": [
            {"role": "assistant", "content": explanation, "format": "text"}
        ],
        "advice_metadata": {
            "risk_profile": sim_req.get("risk_profile", "balanced"),
            "disclaimers": ["Educational only, not financial advice."],
            "sources": []
        },
        "analytics": sim_res
    }
