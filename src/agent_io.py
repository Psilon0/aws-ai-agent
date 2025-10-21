"""
I/O helpers for schemas and message construction.

PURPOSE: Central place for JSON schema validation and message formatting used across
         the FinSense agent and API pipeline.
CONTEXT: Ensures all inputs/outputs conform to defined schemas and provides consistent
         system/user message formatting.
CREDITS: Original work — no external code reuse.
NOTE: Functionality unchanged; comments/docstrings only.
"""

from __future__ import annotations

import json
import pathlib
from functools import lru_cache
from typing import Any, Dict

from jsonschema import Draft7Validator, ValidationError


# -------------------- Schema loading utilities -------------------- #

@lru_cache(maxsize=64)
def _load_schema_cached(abs_path: str) -> Dict[str, Any]:
    """
    Read and parse a JSON schema file, caching it to avoid repeated disk I/O.

    parameters:
    - abs_path: str – full absolute path to the schema file.

    returns:
    - dict – parsed JSON schema content.

    notes:
    - Cached using functools.lru_cache to reduce repeated reads for the same path.
    """
    p = pathlib.Path(abs_path)
    text = p.read_text(encoding="utf-8")
    return json.loads(text)


def load_schema(path: str) -> Dict[str, Any]:
    """
    Load a JSON schema from a relative or absolute path (with caching).

    parameters:
    - path: str – relative or absolute path to schema.

    returns:
    - dict – schema as a Python dictionary.

    raises:
    - FileNotFoundError – if file cannot be located.
    - json.JSONDecodeError – if the file is not valid JSON.

    notes:
    - Falls back to searching from the current working directory if the direct path fails.
    """
    p = pathlib.Path(path)
    if not p.exists():
        # Fallback: try from project root in case current working directory differs.
        alt = pathlib.Path.cwd().joinpath(path)
        if not alt.exists():
            raise FileNotFoundError(f"Schema not found at: {path}")
        p = alt
    return _load_schema_cached(str(p.resolve()))


# -------------------- Validation helpers -------------------- #

def validate_with_schema(instance: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a given instance against a provided schema.

    parameters:
    - instance: dict – data to validate.
    - schema: dict – JSON schema definition.

    raises:
    - ValidationError – if instance fails to meet schema requirements.
    """
    Draft7Validator(schema).validate(instance)


def validate_sim_request(payload: Dict[str, Any]) -> None:
    """
    Validate a simulation request payload against its schema.
    Ensures all required fields are present and correctly typed.
    """
    schema = load_schema("schemas/sim_request.schema.json")
    validate_with_schema(payload, schema)


def validate_sim_result(result: Dict[str, Any]) -> None:
    """
    Validate the result returned from a simulation function or model.
    """
    schema = load_schema("schemas/sim_result.schema.json")
    validate_with_schema(result, schema)


def validate_agent_output(agent_output: Dict[str, Any]) -> None:
    """
    Validate the final agent output to confirm it matches the defined schema.
    """
    schema = load_schema("schemas/agent_output.schema.json")
    validate_with_schema(agent_output, schema)


# -------------------- Message construction helpers -------------------- #

def make_ok_message(content: str) -> Dict[str, str]:
    """
    Create a basic assistant-style message (role='assistant').
    Used for confirming successful operations.
    """
    return {"role": "assistant", "content": str(content)}


def make_user_message(content: str) -> Dict[str, str]:
    """
    Create a user-style message (role='user').
    Ensures message consistency between UI and backend.
    """
    return {"role": "user", "content": str(content)}


def error_to_string(err: Exception) -> str:
    """
    Convert exceptions into readable strings for user-facing error messages.

    parameters:
    - err: Exception – the caught exception.

    returns:
    - str – descriptive message with optional JSON path if ValidationError.

    notes:
    - ValidationError messages include a pointer path showing where validation failed.
    """
    if isinstance(err, ValidationError):
        # Include JSON path context (e.g. $.user.id)
        path = "$" + "".join(f"[{repr(p)}]" if isinstance(p, int) else f".{p}" for p in err.path)
        return f"{err.message} at {path}"
    return f"{type(err).__name__}: {err}"


# -------------------- Public exports -------------------- #

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
