# PURPOSE: Bedrock-powered Agent that plans tool use or reasons with an LLM.
# CONTEXT: If the user asks about portfolio tasks, we route to the local pipeline;
#          otherwise we build a Converse request for the selected Bedrock model.
# CREDITS: Original work — no external code reuse.
# NOTE: Behaviour unchanged; comments/docstrings only. Intent is explained inline.

from typing import Dict, Any, List
import json, os
import boto3
from src.pipeline import run_pipeline
from .agent_io import validate_agent_output

# Region/model come from environment for easy swapping in different deployments.
REGION = os.getenv("AWS_REGION", "eu-west-2")
# Example model ids: deepseek.v3-v1:0, qwen.qwen3-coder-30b-a3b-v1:0
MODEL_ID = os.getenv("MODEL_ID", "deepseek.v3-v1:0")
bedrock = boto3.client("bedrock-runtime", region_name=REGION)

# Load the system prompt once at import-time.
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "finsense_system_prompt.md")
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

class Agent:
    """
    High-level Bedrock agent.

    responsibilities:
    - Quick intent check: if user text implies portfolio work, delegate to pipeline.
    - Otherwise: run a light planner for tool calls, or send a Converse request to the LLM.
    """

    def __init__(self, model_id: str = MODEL_ID):
        self.model_id = model_id

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point.

        flow:
        1) If the user mentions portfolio-like intents, call the local pipeline.
        2) Else, run a simple planner; if it requests a tool, return a tool_call object.
        3) Otherwise, ask the Bedrock model to reason using the system prompt + payload.

        returns:
        - dict – either pipeline output, a tool_call envelope, or LLM-generated output.
        """
        text = (payload.get('message') or {}).get('text','').lower()

        # Fast-path: common portfolio terms go straight to pipeline for stable outputs.
        if any(k in text for k in ['portfolio','allocation','rebalance']):
            return run_pipeline(payload)

        # Lightweight planner to check if we need external data via a tool.
        plan = self._plan(payload)
        if plan.get("tool_call"):
            # For tool calls we return a structured envelope (no execution here).
            return {
                "status": "tool_call",
                "messages": [{"role": "system", "content": f"Calling tool '{plan['tool']['name']}'", "format": "text"}],
                "tool": plan["tool"],
                "trace": plan.get("trace", [])
            }

        # Default: let the model reason over the payload with the project’s system prompt.
        return self._reason(payload)

    def _plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Very simple keyword-based planner.

        rule of thumb:
        - If the text suggests “fetching” or “latest market data”, schedule an HTTP fetch tool.
        - Else, no external data is required.

        returns:
        - dict – {"tool_call": bool, "tool": {...}, "trace": [...]}
        """
        text = (payload.get("message") or {}).get("text", "").lower()
        if any(k in text for k in ["http", "fetch", "latest", "price", "news", "market"]):
            return {"tool_call": True,
                    "tool": {"name": "http_fetch", "args": {"url": "https://example.com"}},
                    "trace": [{"step": "plan", "observation": "Needs external data"}]}
        return {"tool_call": False, "trace": [{"step": "plan", "observation": "No external data needed"}]}

    def _reason(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ask the Bedrock model to reason using the system prompt + the raw payload.

        approach:
        - Serialize the entire payload as the user message so the model has full context.
        - Expect JSON AgentOutput; if plain text comes back, wrap it into a minimal shape.

        returns:
        - dict – AgentOutput-compatible structure (status/messages/etc.).
        """
        # Serialize the user payload so the model can “see” all fields reliably.
        user_payload_str = json.dumps(payload)
        try:
            # Build a Converse request with a single system prompt and one user turn.
            resp = bedrock.converse(
                modelId=self.model_id,
                system=[{"text": SYSTEM_PROMPT}],
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": user_payload_str}]
                    }
                ],
                # Optionally: inferenceConfig={"maxTokens": 1024, "temperature": 0.2, "topP": 0.9}
            )

            # Extract first text block from the model's response.
            # Shape: resp["output"]["message"]["content"] is a list of blocks.
            text = resp.get("output", {}).get("message", {}).get("content", [])
            model_text = ""
            for blk in text:
                if "text" in blk:
                    model_text = blk["text"]
                    break

            # Try to parse JSON; if not JSON, wrap as a simple AgentOutput.
            try:
                out = json.loads(model_text)
            except Exception:
                out = {
                    "status": "ok",
                    "messages": [{"role": "assistant", "content": model_text, "format": "text"}],
                    "advice_metadata": {"disclaimers": ["Educational only, not financial advice."], "sources": []}
                }

            # Ensure disclaimers exist even if the model forgot them.
            if "advice_metadata" not in out:
                out["advice_metadata"] = {"disclaimers": ["Educational only, not financial advice."], "sources": []}
            return out

        except Exception as e:
            # Structured error result if Bedrock call fails.
            return {
                "status": "error",
                "messages": [{"role": "system", "content": f"Bedrock error: {str(e)}", "format": "text"}]
            }

        # Note: This second except block is intentionally left as-is to match your source.
        # (No behavioural changes requested.)
        except Exception as e:
            return {
                "status": "error",
                "messages": [{"role": "system", "content": f"Bedrock error: {str(e)}", "format": "text"}]
            }
