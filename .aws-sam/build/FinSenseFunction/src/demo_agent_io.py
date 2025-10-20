from agent_io import validate_agent_input, make_ok_message, make_tool_call

agent_input = {
  "session_id": "sess_123",
  "user": {"id": "rafe", "role": "user"},
  "message": {"text": "Summarise latest FTSE news"},
  "context": {"time_iso": "2025-10-14T10:00:00Z", "locale": "en-GB"}
}

errors = validate_agent_input(agent_input)
print("INPUT VALIDATION:", "OK" if not errors else errors)

ok = make_ok_message("Here’s a summary...", fmt="markdown")
print("OK OUTPUT:", ok)

tool = make_tool_call(
    name="http_fetch",
    args={"url": "https://api.example.com/news"},
    system_note="Calling tool 'http_fetch'"
)
print("TOOL CALL OUTPUT:", tool)
