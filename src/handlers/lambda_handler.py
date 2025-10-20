import json
from ..agent_core import Agent

# PURPOSE: AWS Lambda entry point for the FinSense agent.
# CONTEXT: Triggered by API Gateway; wraps Agent.handle() into a Lambda-compatible format.
# CREDITS: Original work — no external reuse.
agent = Agent()

def handler(event, context):
    """
    Lambda handler.
    Converts the AWS event into a payload for the Agent, runs it, and wraps response in JSON.
    """
    try:
        body = event.get("body") if isinstance(event, dict) else None
        payload = json.loads(body) if isinstance(body, str) else (body or event)
        result = agent.handle(payload)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result)
        }
    except Exception as e:
        # Return structured error response if something goes wrong.
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "error",
                "messages": [{
                    "role": "system",
                    "content": str(e),
                    "format": "text"
                }]
            })
        }
