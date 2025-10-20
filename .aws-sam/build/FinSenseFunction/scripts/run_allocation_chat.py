#!/usr/bin/env python3
import json, os
from src.agent_core import Agent

if __name__ == "__main__":
    text = "Please recommend a portfolio allocation for a balanced risk profile over 5 years."
    payload = {
        "session_id": "local",
        "user": {"id": "rafe", "role": "user"},
        "message": {"text": text},
        "context": {"risk_profile":"balanced","horizon_years":5, "locale":"en-GB"}
    }
    out = Agent().handle(payload)
    print(json.dumps(out, indent=2))
