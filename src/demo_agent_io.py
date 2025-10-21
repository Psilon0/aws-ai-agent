# PURPOSE: Local test for validating schema functions and message construction helpers.
# CONTEXT: Demonstrates how to use agent_io functions for schema validation,
#          message formatting, and simulated tool call creation.
# CREDITS: Original work — no external code reuse.
# NOTE: Logic unchanged; comments/docstrings only.

from agent_io import validate_agent_input, make_ok_message, make_tool_call

# Example input following the AgentInput schema.
# Represents a user asking for a FTSE summary through the conversational agent.
agent_input = {
  "session_id": "sess_123",
  "user": {"id": "rafe", "role": "user"},
  "message": {"text": "Summarise latest FTSE news"},
  "context": {"time_iso": "2025-10-14T10:00:00Z", "locale": "en-GB"}
}

# Validate the input against the schema.
# validate_agent_input() should return an empty list (no errors) if the structure is valid.
errors = validate_agent_input(agent_input)
print("INPUT VALIDATION:", "OK" if not errors else errors)

# Construct a standard assistant message in Markdown format.
# make_ok_message() wraps content with the correct "role" and format.
ok = make_ok_message("Here’s a summary...", fmt="markdown")
print("OK OUTPUT:", ok)

# Construct a simulated tool call message.
# make_tool_call() builds a system message that describes a tool invocation request.
tool = make_tool_call(
    name="http_fetch",
    args={"url": "https://api.example.com/news"},
    system_note="Calling tool 'http_fetch'"
)
print("TOOL CALL OUTPUT:", tool)
