#!/usr/bin/env python3
import json, sys
from src.agent_core import Agent

agent = Agent()

print("FinSense CLI — type your message and press Enter. Ctrl+C to exit.")
while True:
    try:
        text = input("> ")
        payload = {"session_id": "local",
                   "user": {"id": "rafe", "role": "user"},
                   "message": {"text": text},
                   "context": {"locale": "en-GB"}}
        out = agent.handle(payload)
        print(json.dumps(out, indent=2))
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")
        sys.exit(0)
