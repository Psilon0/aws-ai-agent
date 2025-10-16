from typing import Dict, Any
from .agent_core import Agent

_agent = Agent()

def route(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _agent.handle(payload)
