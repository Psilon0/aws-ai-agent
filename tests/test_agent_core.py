from src.agent_core import Agent

def test_plan_no_tool():
    a = Agent(model_id="test-model")
    payload = {"message": {"text": "hello there"}}
    plan = a._plan(payload)
    assert plan["tool_call"] is False

def test_plan_with_tool_keywords():
    a = Agent(model_id="test-model")
    payload = {"message": {"text": "latest market news please"}}
    plan = a._plan(payload)
    assert plan["tool_call"] is True
