from __future__ import annotations
import json
from src.agent import Agent

_agent = Agent()

def handler(event, context):
    try:
        body = event.get("body")
        payload = json.loads(body) if isinstance(body, str) else (body or {})
        result = _agent.handle(payload)
        return {"statusCode": 200, "headers": {"Content-Type":"application/json"}, "body": json.dumps(result)}
    except Exception as e:
        return {"statusCode": 400, "headers": {"Content-Type":"application/json"},
                "body": json.dumps({"error": str(e)})}
