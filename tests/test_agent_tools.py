from src.agent import Agent

def test_agent_http_tool_execution(monkeypatch):
    """Ensure http_tool fetch executes when fetch_url is given."""
    agent = Agent()

    # Mock the tool
    called = {}
    monkeypatch.setattr("src.tools.http_tool.fetch", lambda url: {"mocked": url, "ok": True, "called": called.setdefault("yes", True)})

    payload = {"fetch_url": "https://example.com"}
    out = agent.handle(payload)

    assert out["status"] == "ok"
    assert "tool_result" in out
    assert out["tool_result"]["ok"] is True
    assert called  # ensure mock executed
    assert out["messages"][0]["content"].startswith("Tool 'http_tool'")
