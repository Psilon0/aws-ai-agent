import json
from ..agent_core import Agent

agent = Agent()

def handler(event, context):
    try:
        body = event.get("body") if isinstance(event, dict) else None
        payload = json.loads(body) if isinstance(body, str) else (body or event)
        result = agent.handle(payload)
        return {"statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(result)}
    except Exception as e:
        return {"statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"status": "error",
                                    "messages": [{"role": "system", "content": str(e), "format": "text"}]})}
