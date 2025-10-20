import json
from pathlib import Path
from typing import Any, Dict, List
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
INPUT_SCHEMA_PATH = ROOT / "schemas" / "agent_input.schema.json"
OUTPUT_SCHEMA_PATH = ROOT / "schemas" / "agent_output.schema.json"

def _load_schema(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

_input_validator = Draft202012Validator(_load_schema(INPUT_SCHEMA_PATH))
_output_validator = Draft202012Validator(_load_schema(OUTPUT_SCHEMA_PATH))

def validate_agent_input(payload: Dict[str, Any]) -> List[str]:
    """Returns a list of human-friendly error strings (empty list means valid)."""
    errors = []
    for err in _input_validator.iter_errors(payload):
        loc = " / ".join(map(str, err.absolute_path)) or "(root)"
        errors.append(f"{loc}: {err.message}")
    return errors

def validate_agent_output(payload: Dict[str, Any]) -> List[str]:
    errors = []
    for err in _output_validator.iter_errors(payload):
        loc = " / ".join(map(str, err.absolute_path)) or "(root)"
        errors.append(f"{loc}: {err.message}")
    return errors

# Convenience constructors to keep model-facing schema small and explicit
def make_ok_message(text: str, fmt: str = "markdown") -> Dict[str, Any]:
    payload = {
        "status": "ok",
        "messages": [
            {"role": "assistant", "content": text, "format": fmt}
        ]
    }
    errs = validate_agent_output(payload)
    if errs:
        raise ValueError("Invalid AgentOutput: " + "; ".join(errs))
    return payload

def make_tool_call(name: str, args: Dict[str, Any], system_note: str) -> Dict[str, Any]:
    payload = {
        "status": "tool_call",
        "messages": [
            {"role": "system", "content": system_note, "format": "text"}
        ],
        "tool": {"name": name, "args": args},
        "trace": [{"step": "plan", "observation": "tool selected"}]
    }
    errs = validate_agent_output(payload)
    if errs:
        raise ValueError("Invalid AgentOutput: " + "; ".join(errs))
    return payload
