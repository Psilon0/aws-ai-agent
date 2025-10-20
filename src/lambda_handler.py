"""
AWS Lambda handler: validates input, calls Agent, returns schema-valid output.
Adds structured, JSON CloudWatch-friendly logs with correlation IDs.
"""

from __future__ import annotations
import json
import time
import traceback
import uuid
from typing import Any, Dict

from src.logging_setup import configure_logging
from src.agent import Agent
from src.agent_io import make_ok_message, load_schema
from jsonschema import validate, ValidationError


log = configure_logging()


def _response(body: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    # API Gateway compatible wrapper (if used behind HTTP)
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    t0 = time.time()
    request_id = getattr(context, "aws_request_id", None) or str(uuid.uuid4())
    correlation_id = (event.get("headers", {}) or {}).get("x-correlation-id") or str(uuid.uuid4())

    log.bind(request_id=request_id, correlation_id=correlation_id).info("request.received", event_type=type(event).__name__)

    # Normalize body (when triggered by API Gateway)
    body = event
    if isinstance(event, dict) and "body" in event:
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else (event["body"] or {})
        except Exception:
            body = {}
            log.warning("request.body_parse_failed")

    # Call the Agent
    try:
        agent = Agent()
        result = agent.handle(body)

        # Validate final output if schema exists
        try:
            schema = load_schema("schemas/agent_output.schema.json")
            validate(result, schema)
        except (FileNotFoundError, ValidationError) as e:
            # If invalid, turn into an error payload but still return 200 to avoid API GW retries
            latency_ms = round((time.time() - t0) * 1000, 1)
            err_payload = {
                "status": "error",
                "messages": [make_ok_message(f"AgentOutput schema violation: {str(e)}")],
                "latency_ms": latency_ms,
                "trace": result.get("trace", []),
            }
            log.error("response.schema_invalid", error=str(e), latency_ms=latency_ms)
            return _response(err_payload, 200)

        latency_ms = round((time.time() - t0) * 1000, 1)
        log.info("response.success", latency_ms=latency_ms)
        return _response(result, 200)

    except Exception as e:
        latency_ms = round((time.time() - t0) * 1000, 1)
        log.error(
            "response.error",
            error=str(e),
            traceback=traceback.format_exc(limit=2),
            latency_ms=latency_ms,
        )
        # Schema-valid error body
        error_body = {
            "status": "error",
            "messages": [make_ok_message(f"{type(e).__name__}: {e}")],
            "latency_ms": latency_ms,
        }
        return _response(error_body, 200)
