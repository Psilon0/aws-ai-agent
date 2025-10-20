from typing import Dict, Any, List
import os, json
import boto3
from jsonschema import validate as json_validate, ValidationError
from src.tools.analytics_stub import run_simulation

# Load prompts
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
with open(os.path.join(PROMPTS_DIR, "sim_request_prompt.md"), "r", encoding="utf-8") as f:
    SIM_PROMPT = f.read()
with open(os.path.join(PROMPTS_DIR, "final_explainer_prompt.md"), "r", encoding="utf-8") as f:
    EXPLAIN_PROMPT = f.read()

# Load schemas
SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
with open(os.path.join(SCHEMAS_DIR, "sim_request.schema.json"), "r", encoding="utf-8") as f:
    SIM_REQ_SCHEMA = json.load(f)
with open(os.path.join(SCHEMAS_DIR, "sim_result.schema.json"), "r", encoding="utf-8") as f:
    SIM_RES_SCHEMA = json.load(f)

REGION = os.getenv("AWS_REGION", "eu-west-2")
MODEL_ID = os.getenv("MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

def _converse(system_text: str, user_obj: Dict[str, Any]) -> str:
    """Call Bedrock Converse with a system prompt and a single user JSON payload; return first text block."""
    body = {
        "modelId": MODEL_ID,
        "system": [{"text": system_text}],
        "messages": [
            {
                "role": "user",
                "content": [{"text": json.dumps(user_obj)}],
            }
        ],
        # "inferenceConfig": {"maxTokens": 1024, "temperature": 0.2, "topP": 0.9},
    }
    resp = bedrock.converse(
        modelId=MODEL_ID,
        system=body["system"],
        messages=body["messages"],
        # inferenceConfig=body.get("inferenceConfig")
    )
    content = resp.get("output", {}).get("message", {}).get("content", [])
    for blk in content:
        if "text" in blk:
            return blk["text"]
    return ""

def _make_sim_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = (payload.get("message") or {}).get("text", "")
    ctx  = payload.get("context") or {}
    hints = {
        "risk_profile": ctx.get("risk_profile", "balanced"),
        "horizon_years": int(ctx.get("horizon_years", 5)),
        "notes": "defaults from context"
    }
    user_obj = {"message": text, "hints": hints}
    out_text = _converse(SIM_PROMPT, user_obj)
    try:
        sim_req = json.loads(out_text)
        json_validate(sim_req, SIM_REQ_SCHEMA)
        return sim_req
    except Exception:
        # Fall back to hints if the model didn't return strict JSON
        return hints

def _explain_result(sim_req: Dict[str, Any], sim_res: Dict[str, Any]) -> str:
    user_obj = {"request": sim_req, "result": sim_res}
    return _converse(EXPLAIN_PROMPT, user_obj)

def run_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    # 1) Plan a SimRequest via Bedrock
    sim_req = _make_sim_request(payload)

    # 2) Call simulator (stub for now; replace later)
    sim_res = run_simulation(sim_req)
    try:
        json_validate(sim_res, SIM_RES_SCHEMA)
    except ValidationError as e:
        raise RuntimeError(f"Simulator result failed schema: {e.message}")

    # 3) Explain via Bedrock
    explanation = _explain_result(sim_req, sim_res)

    # 4) Wrap into AgentOutput
    return {
        "status": "ok",
        "messages": [{"role": "assistant", "content": explanation, "format": "text"}],
        "advice_metadata": {
            "risk_profile": sim_req.get("risk_profile", "balanced"),
            "disclaimers": ["Educational only, not financial advice."],
            "sources": []
        },
        "analytics": sim_res
    }
