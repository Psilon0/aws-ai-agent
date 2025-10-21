"""
Pipeline for FinSense — runs the simulation + formats advice.

PURPOSE:
- Validate a simulation request, run the deterministic simulator, validate its output,
  generate a concise advisory summary, and package everything into a stable AgentOutput.

CONTEXT:
- Called by the Agent when portfolio analytics are requested. Keeps responses deterministic
  and schema-compliant for coursework marking and reproducibility.

CREDITS:
- Original work — no external code reuse.
NOTE:
- Behaviour unchanged; comments/docstrings only.
"""

import json
import time
import uuid
import os
from typing import Dict, Any
from jsonschema import validate, ValidationError
from src import tools


def run_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main orchestrator for simulation and explanation.

    steps:
    1) Validate input against the sim_request schema.
    2) Run the deterministic simulator (no Bedrock here).
    3) Validate the simulator's output against its schema.
    4) Generate short advice text (optionally via Bedrock if enabled).
    5) Package a final AgentOutput with run_id and latency.

    parameters:
    - payload: dict – expected to match schemas/sim_request.schema.json.

    returns:
    - dict – AgentOutput-style response including advice, allocation, KPIs, and latency.
             On validation or runtime errors, returns a minimal {"status":"error", "messages":[...]}.
    """
    start = time.time()

    # 1) Validate input against sim_request schema
    from src.agent_io import load_schema
    try:
        sim_request_schema = load_schema("schemas/sim_request.schema.json")
        validate(payload, sim_request_schema)
    except (FileNotFoundError, ValidationError) as e:
        return {"status": "error", "messages": [f"Invalid sim request: {e}"]}

    # 2) Run the deterministic simulator (always runs; no Bedrock here)
    try:
        sim_result = tools.analytics_stub.run_simulation(payload)
    except Exception as e:
        return {"status": "error", "messages": [f"Simulation failed: {e}"]}

    # 3) Validate simulator output
    try:
        sim_result_schema = load_schema("schemas/sim_result.schema.json")
        validate(sim_result, sim_result_schema)
    except (FileNotFoundError, ValidationError) as e:
        return {"status": "error", "messages": [f"Simulator output invalid: {e}"]}

    # 4) Generate advice text (Bedrock optional; respects USE_BEDROCK=0)
    advice_text = _explain_result(sim_result)
    advice_text = _cap_words(advice_text, max_words=180)

    # 5) Package final AgentOutput
    run_id = str(uuid.uuid4())
    latency_ms = round((time.time() - start) * 1000, 1)

    allocation = sim_result.get("proposed_allocation") or sim_result.get("allocation")
    kpis = sim_result.get("kpis")

    agent_output = {
        "status": "ok",
        "run_id": run_id,
        "messages": [{"role": "assistant", "content": advice_text}],
        "analytics": sim_result,
        "allocation": allocation,
        "kpis": kpis,
        "advice": {
            "summary": advice_text,
            "one_action": "Review your allocation and adjust if goals change.",
            "disclaimer": "Educational only, not financial advice."
        },
        "latency_ms": latency_ms,
    }

    # Validate final shape if schema exists; errors become a schema-valid "error" response.
    try:
        agent_schema = load_schema("schemas/agent_output.schema.json")
        validate(agent_output, agent_schema)
    except FileNotFoundError:
        pass
    except ValidationError as e:
        return {
            "status": "error",
            "messages": [f"AgentOutput failed schema validation: {e.message}"],
            "analytics": sim_result,
            "latency_ms": latency_ms,
        }

    return agent_output


def _cap_words(text: str, max_words: int) -> str:
    """
    Hard-cap a piece of text at a maximum number of words.

    parameters:
    - text: str – input paragraph/string.
    - max_words: int – limit to enforce.

    returns:
    - str – trimmed string (adds "…" if truncated). Returns empty string for non-strings.
    """
    if not isinstance(text, str):
        return ""
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).rstrip() + "…"


def _converse(prompt_text: str) -> str:
    """
    Optionally call Bedrock to generate explanatory text; otherwise return a stub.

    behaviour:
    - If USE_BEDROCK is "0" (default), return a fixed local explanation.
    - If enabled, call src.tools.bedrock_client.converse(prompt_text) and
      try to coerce the result to a string in a tolerant way.
    - Never raises; always returns fallback text on errors.

    parameters:
    - prompt_text: str – the full prompt built from the explainer template + sim result.

    returns:
    - str – human-readable explanation of the simulated portfolio outcome.
    """
    if os.getenv("USE_BEDROCK", "0") == "0":
        return ("Based on the simulated data, this allocation targets balanced growth with "
                "moderate volatility. Rebalance periodically and keep a small cash buffer.")

    try:
        from src.tools import bedrock_client
        resp = bedrock_client.converse(prompt_text)
        if isinstance(resp, str):
            return resp
        if isinstance(resp, dict):
            msgs = resp.get("messages") or []
            if msgs and isinstance(msgs[0], dict):
                return msgs[0].get("content") or "No response text."
            return resp.get("output") or resp.get("content") or "No response text."
        return str(resp)
    except Exception:
        return ("Based on the simulated data, your portfolio appears balanced for a moderate "
                "risk profile. Consider periodic rebalancing and a small cash buffer.")


def _make_sim_request(risk_profile: str, horizon_years: int, seed: int = 42) -> Dict[str, Any]:
    """
    Build a minimal sim request payload.

    parameters:
    - risk_profile: str – e.g., 'conservative' | 'balanced' | 'aggressive'
    - horizon_years: int – 1..40
    - seed: int – deterministic demo seed (default 42)

    returns:
    - dict – structure compatible with run_simulation().
    """
    # Kept for compatibility if used elsewhere
    return {
        "risk_profile": risk_profile,
        "horizon_years": horizon_years,
        "context": {"demo_seed": seed}
    }


def _explain_result(sim_result: Dict[str, Any]) -> str:
    """
    Build the explainer prompt (from file if available), attach the simulation JSON,
    and obtain a concise natural-language explanation (via Bedrock or local stub).

    parameters:
    - sim_result: dict – the simulator's output.

    returns:
    - str – explanatory paragraph intended for end users.
    """
    try:
        with open("src/prompts/final_explainer_prompt.md", "r") as f:
            base_prompt = f.read()
    except FileNotFoundError:
        base_prompt = "Summarise the portfolio outlook clearly and concisely for a general audience."

    result_text = json.dumps(sim_result, indent=2, sort_keys=True)
    full_prompt = f"{base_prompt}\n\nSimulation result JSON:\n{result_text}"
    return _converse(full_prompt)
