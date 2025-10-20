from typing import Dict, Any, List
import json, os
import boto3
from src.pipeline import run_pipeline
from .agent_io import validate_agent_output

REGION = os.getenv("AWS_REGION", "eu-west-2")
MODEL_ID = os.getenv("MODEL_ID", "deepseek.v3-v1:0")  # e.g. deepseek.v3-v1:0 or qwen.qwen3-coder-30b-a3b-v1:0
bedrock = boto3.client("bedrock-runtime", region_name=REGION)

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "finsense_system_prompt.md")
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

class Agent:
    def __init__(self, model_id: str = MODEL_ID):
        self.model_id = model_id

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = (payload.get('message') or {}).get('text','').lower()
        if any(k in text for k in ['portfolio','allocation','rebalance']):
            return run_pipeline(payload)
        plan = self._plan(payload)
        if plan.get("tool_call"):
            return {
                "status": "tool_call",
                "messages": [{"role": "system", "content": f"Calling tool '{plan['tool']['name']}'", "format": "text"}],
                "tool": plan["tool"],
                "trace": plan.get("trace", [])
            }
        return self._reason(payload)

    def _plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = (payload.get("message") or {}).get("text", "").lower()
        if any(k in text for k in ["http", "fetch", "latest", "price", "news", "market"]):
            return {"tool_call": True,
                    "tool": {"name": "http_fetch", "args": {"url": "https://example.com"}},
                    "trace": [{"step": "plan", "observation": "Needs external data"}]}
        return {"tool_call": False, "trace": [{"step": "plan", "observation": "No external data needed"}]}

    def _reason(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Build a proper Converse request: system prompt in 'system', user content in 'messages'
        user_payload_str = json.dumps(payload)
        try:
            resp = bedrock.converse(
                modelId=self.model_id,
                system=[{"text": SYSTEM_PROMPT}],
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": user_payload_str}]
                    }
                ],
                # You can add inferenceConfig here if you like:
                # inferenceConfig={"maxTokens": 1024, "temperature": 0.2, "topP": 0.9}
            )
            # Converse response shape:
            # resp["output"]["message"]["content"] -> list of blocks, take the first text
            text = resp.get("output", {}).get("message", {}).get("content", [])
            model_text = ""
            for blk in text:
                if "text" in blk:
                    model_text = blk["text"]
                    break
            # Model is expected to produce AgentOutput JSON; try to parse
            try:
                out = json.loads(model_text)
            except Exception:
                # If the model responded with plain text, wrap it into AgentOutput
                out = {
                    "status": "ok",
                    "messages": [{"role": "assistant", "content": model_text, "format": "text"}],
                    "advice_metadata": {"disclaimers": ["Educational only, not financial advice."], "sources": []}
                }
            if "advice_metadata" not in out:
                out["advice_metadata"] = {"disclaimers": ["Educational only, not financial advice."], "sources": []}
            return out
        except Exception as e:
            # Return structured error in AgentOutput shape
            return {
                "status": "error",
                "messages": [{"role": "system", "content": f"Bedrock error: {str(e)}", "format": "text"}]
            }

        except Exception as e:
            # Return structured error in AgentOutput shape
            return {
                "status": "error",
                "messages": [{"role": "system", "content": f"Bedrock error: {str(e)}", "format": "text"}]
            }

