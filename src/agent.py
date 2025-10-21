"""
Agent core logic: interprets user input, plans actions, calls tools if needed.

PURPOSE: High-level controller that decides whether to invoke a tool or run the
         portfolio pipeline, and records a lightweight trace.
CONTEXT: Used by both CLI and API backends in FinSense.
CREDITS: Original work — no external code reuse.
NOTE: Behaviour unchanged; comments/docstrings only.
"""

import json
import traceback
import os
from typing import Dict, Any

from src import tools
from src.agent_io import make_ok_message, error_to_string
from src import state_manager as sm


class Agent:
    """High-level controller for FinSense Agent."""

    def __init__(self):
        # In-memory trace of key planning/execution steps for debugging or audits.
        self.trace = []

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point. Handles user or system payloads and dispatches to tools or pipeline.

        parameters:
        - payload: dict – can include 'fetch_url' to force an http tool call, or a normal
          request expected by the pipeline.

        returns:
        - dict – structured result. On tool calls, includes 'tool_result'; otherwise returns
          the pipeline's output shape (advice, allocation, etc.). Always includes 'trace'.

        notes:
        - If a 'session_id' is present (or provided via env), a short trace is persisted
          via the state manager. Persistence failures never block the main flow.
        """
        try:
            plan = self._plan(payload)
            self.trace.append(plan)

            # Optional persistence: attach planning step to a session, if provided.
            session_id = (payload.get("session_id") if isinstance(payload, dict) else None) or os.getenv("SESSION_ID")
            if session_id:
                try:
                    if sm.get_session(session_id) is None:
                        sm.init_session(session_id, meta={"created_by": "Agent"})
                    sm.append_trace(session_id, {"event": "plan", "data": plan})
                except Exception:
                    # Never fail the user request because session storage had an issue.
                    pass

            # Tool execution branch: when the planner requests a tool.
            if plan.get("tool_call"):
                tool_name = plan.get("tool")
                args = plan.get("args", {})
                result = self._execute_tool(tool_name, args)

                out = {
                    "status": "ok",
                    "messages": [make_ok_message(f"Tool '{tool_name}' executed successfully.")],
                    "tool_result": result,
                    "trace": self.trace,
                }
                if session_id:
                    try:
                        sm.append_trace(session_id, {"event": "tool_result", "data": result})
                    except Exception:
                        pass
                return out

            # Default: delegate to the simulation/analysis pipeline.
            from src.pipeline import run_pipeline
            agent_output = run_pipeline(payload)
            agent_output["trace"] = self.trace
            if session_id:
                try:
                    sm.append_trace(session_id, {"event": "pipeline_result_meta", "data": {"status": agent_output.get("status")}})
                except Exception:
                    pass
            return agent_output

        except Exception as e:
            # Return a structured error with a short, user-facing message and a compact traceback.
            tb = traceback.format_exc(limit=2)
            return {
                "status": "error",
                "messages": [make_ok_message(error_to_string(e)), {"role": "system", "content": tb}],
                "trace": self.trace,
            }

    def _plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Very simple, rule-based planner (stub).

        rules:
        - If the payload contains 'fetch_url', call the HTTP tool.
        - Otherwise, proceed to the pipeline.

        returns:
        - dict – e.g., {"tool": "...", "tool_call": True, "args": {...}} or {"tool_call": False, "next": "pipeline"}.
        """
        if isinstance(payload, dict) and "fetch_url" in payload:
            return {
                "tool": "http_tool",
                "tool_call": True,
                "args": {"url": payload["fetch_url"]}
            }
        return {"tool_call": False, "next": "pipeline"}

    def _execute_tool(self, name: str, args: Dict[str, Any]):
        """
        Route to the correct tool and execute it safely.

        parameters:
        - name: str – registered tool name (e.g., 'http_tool', 'analytics_stub', 's3_tool', 'dynamodb_tool').
        - args: dict – keyword arguments passed directly to the tool.

        returns:
        - Any – whatever the tool returns (often a dict or primitive).

        raises:
        - RuntimeError – wraps any underlying error with the tool name for easier debugging.
        """
        try:
            if name == "http_tool":
                url = args.get("url")
                return tools.http_tool.fetch(url)

            elif name == "analytics_stub":
                return tools.analytics_stub.run_simulation(args)

            elif name == "s3_tool":
                return tools.s3_tool.put_json(**args)

            elif name == "dynamodb_tool":
                return tools.dynamodb_tool.put_item(**args)

            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            # Provide context about which tool failed; keep original exception as cause.
            raise RuntimeError(f"Tool '{name}' failed: {e}") from e
