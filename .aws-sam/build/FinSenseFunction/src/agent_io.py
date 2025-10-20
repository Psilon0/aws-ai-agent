"""
I/O helpers for schemas and message construction.
"""

from __future__ import annotations

import json
import pathlib
from functools import lru_cache
from typing import Any, Dict

from jsonschema import Draft7Validator, ValidationError


# -------------------------- Schema loading ---------------------------------- #

@lru_cache(maxsize=64)
def _load_schema_cached(abs_path: str) -> Dict[str, Any]:
    p = pathlib.Path(abs_path)
    text = p.read_text(encoding="utf-8")
    return json.loads(text)


def load_schema(path: str) -> Dict[str, Any]:
    """
    Load a JSON schema from a relative or absolute path with small cache.
    Raises FileNotFoundError / JSONDecodeError on problems.
    """
    p = pathlib.Path(path)
    if not p.exists():
        # Try from project root if called from a different CWD
        alt = pathlib.Path.cwd().joinpath(path)
        if not alt.exists():
            raise FileNotFoundError(f"Schema not found at: {path}")
        p = alt
    return _load_schema_cached(str(p.resolve()))


# -------------------------- Validators -------------------------------------- #

def validate_with_schema(instance: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate instance against a schema. Raises ValidationError on failure.
    """
    Draft7Validator(schema).validate(instance)


def validate_sim_request(payload: Dict[str, Any]) -> None:
    schema = load_schema("schemas/sim_request.schema.json")
    validate_with_schema(payload, schema)


def validate_sim_result(result: Dict[str, Any]) -> None:
    schema = load_schema("schemas/sim_result.schema.json")
    validate_with_schema(result, schema)


def validate_agent_output(agent_output: Dict[str, Any]) -> None:
    schema = load_schema("schemas/agent_output.schema.json")
    validate_with_schema(agent_output, schema)


# -------------------------- Message helpers --------------------------------- #

def make_ok_message(content: str) -> Dict[str, str]:
    return {"role": "assistant", "content": str(content)}


def make_user_message(content: str) -> Dict[str, str]:
    return {"role": "user", "content": str(content)}


def error_to_string(err: Exception) -> str:
    if isinstance(err, ValidationError):
        # Include pointer to where it failed if available
        path = "$" + "".join(f"[{repr(p)}]" if isinstance(p, int) else f".{p}" for p in err.path)
        return f"{err.message} at {path}"
    return f"{type(err).__name__}: {err}"


__all__ = [
    "load_schema",
    "validate_with_schema",
    "validate_sim_request",
    "validate_sim_result",
    "validate_agent_output",
    "make_ok_message",
    "make_user_message",
    "error_to_string",
]
