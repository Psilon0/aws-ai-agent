#!/usr/bin/env python3
# PURPOSE: Simple command-line interface (CLI) to talk with the FinSense Agent.
# CONTEXT: Lets you test the agent locally without the Streamlit front end.
# CREDITS: Original work — no reused or adapted external code.

import json, sys
from src.agent_core import Agent

# Create an instance of the Agent class (handles all logic for user requests).
agent = Agent()

# Welcome message so the user knows how to use the CLI.
print("FinSense CLI — type your message and press Enter. Ctrl+C to exit.")

# Continuous input loop for live conversation.
while True:
    try:
        # Prompt user for input text.
        text = input("> ")

        # Build a structured payload similar to what the backend would receive.
        # This ensures the CLI behaves like the deployed version of the system.
        payload = {
            "session_id": "local",              # Marks this session as local only (not persistent)
            "user": {"id": "rafe", "role": "user"},  # Basic user info for tracking or logging
            "message": {"text": text},          # The actual user message being sent
            "context": {"locale": "en-GB"}      # Optional context like language or region
        }

        # Pass the payload to the Agent and capture its structured response.
        out = agent.handle(payload)

        # Pretty-print the agent’s JSON output for easier reading in the terminal.
        print(json.dumps(out, indent=2))

    # Gracefully handle end-of-input or Ctrl+C so the program exits cleanly.
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")
        sys.exit(0)
