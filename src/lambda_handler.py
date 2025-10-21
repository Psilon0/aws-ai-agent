"""
AWS Lambda handler: validates input, calls Agent, returns schema-valid output.
Adds structured, JSON CloudWatch-friendly logs with correlation IDs.

PURPOSE:
- Entry point for AWS Lambda behind API Gateway.
- Normalises the incoming event, delegates to Agent, validates output against schema,
  and returns an HTTP-style response body.

CONTEXT:
- Used by the deployed FinSense API. Logging includes request_id and correlation_id
  so traces are easy to follow in CloudWatch.

CREDITS:
- Original work — no external code reuse.

NOTE:
- Behaviour unchanged. Comments/docstrings only.
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


# Configure a structured logger once; emits JSON-like key/value logs.
log = configure_logging()


def _response(body: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """
    Wrap a Python dict into an API Gateway compatible response.

    parameters:
    - body: dict – payload to serialise as JSON.
    - status_code: int – HTTP status code to return (defaults to 200).

    returns:
    - dict – {"statusCode": int, "headers": {...}, "body": "<json-string>"}.
    """
    # API Gateway compatible wrapper (if used behind HTTP)
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Lambda entry point.

    flow:
    1) Bind request/correlation IDs for traceability.
    2) Normalise body (handles API Gateway proxy format if present).
    3) Create Agent and call handle(body).
    4) Validate result against AgentOutput schema (if available).
       - If schema fails, return a schema-valid error payload (still HTTP 200 to avoid retries).
    5) On unhandled exceptions, return a schema-valid "error" payload and log traceback.

    returns:
    - dict – API Gateway compatible response with JSON body.
    """
    t0 = time.time()

    # Prefer AWS-provided request id; otherwise generate one. Correlation id can be
    # passed by callers (e.g., API Gateway header) to tie multiple services together.
    request_id = getattr(context, "aws_request_id", None) or str(uuid.uuid4())
    correlation_id = (event.get("headers", {}) or {}).get("x-correlation-id") or str(uuid.uuid4())

    log.bind(request_id=request_id, correlation_id=correlation_id).info(
        "request.received", event_type=type(event).__name__
    )

    # Normalise body (when triggered by API Gateway proxy integration).
    # If event["body"] is a JSON string, parse it; otherwise fall back to {} on error.
    body = event
    if isinstance(event, dict) and "body" in event:
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else (event["body"] or {})
        except Exception:
            body = {}
            log.warning("request.body_parse_failed")

    # Call the Agent and optionally validate the final payload.
    try:
        agent = Agent()
        result = agent.handle(body)

        # Validate final output if schema exists. Keeping response shape consistent is
        # helpful for downstream consumers and tests.
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

        # Success path: log latency and return the agent’s result.
        latency_ms = round((time.time() - t0) * 1000, 1)
        log.info("response.success", latency_ms=latency_ms)
        return _response(result, 200)

    except Exception as e:
        # Ensure we always return a schema-valid error shape, even on unexpected failures.
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
