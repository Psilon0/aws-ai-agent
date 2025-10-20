"""
Agent core logic: interprets user input, plans actions, calls tools if needed.
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
        self.trace = []

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point. Handles user or system payloads and dispatches to tools or pipeline.
        """
        try:
            plan = self._plan(payload)
            self.trace.append(plan)

            # --- Optional persistence: attach to session if provided ---
            session_id = (payload.get("session_id") if isinstance(payload, dict) else None) or os.getenv("SESSION_ID")
            if session_id:
                try:
                    if sm.get_session(session_id) is None:
                        sm.init_session(session_id, meta={"created_by": "Agent"})
                    sm.append_trace(session_id, {"event": "plan", "data": plan})
                except Exception:
                    # Don't block the main flow on persistence issues
                    pass

            # --- Tool execution branch ---
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

            # --- Default: delegate to pipeline ---
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
            tb = traceback.format_exc(limit=2)
            return {
                "status": "error",
                "messages": [make_ok_message(error_to_string(e)), {"role": "system", "content": tb}],
                "trace": self.trace,
            }

    # ---------------------------------------------------------------------- #
    # Planning phase (stub: in reality this might call an LLM)
    # ---------------------------------------------------------------------- #
    def _plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Basic rule-based planner stub:
        - If payload includes 'fetch_url', call http_tool
        - Otherwise, send to simulation pipeline
        """
        if isinstance(payload, dict) and "fetch_url" in payload:
            return {
                "tool": "http_tool",
                "tool_call": True,
                "args": {"url": payload["fetch_url"]}
            }
        return {"tool_call": False, "next": "pipeline"}

    # ---------------------------------------------------------------------- #
    # Tool execution layer
    # ---------------------------------------------------------------------- #
    def _execute_tool(self, name: str, args: Dict[str, Any]):
        """Route to the correct tool and execute it safely."""
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
            raise RuntimeError(f"Tool '{name}' failed: {e}") from e
