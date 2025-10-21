"""
Session state manager for FinSense.

PURPOSE:
- Provides lightweight session persistence using DynamoDB.
- Each session stores a simple state, trace history, and a TTL (time-to-live)
  for automatic cleanup after a set number of days.

CONTEXT:
- Used by Agent and Lambda handler to store per-user or per-run context.
- Works safely even if called concurrently across multiple Lambda executions.

CREDITS:
- Original work — no external code reuse.
NOTE:
- Logic unchanged; comments/docstrings only.
"""

from __future__ import annotations
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
import os
from src.tools import dynamodb_tool as ddb


# Default number of days to retain session records before DynamoDB expiry.
DEFAULT_TTL_DAYS = int(os.getenv("SESSION_TTL_DAYS", "14"))


def _ttl_epoch(days: int = DEFAULT_TTL_DAYS) -> int:
    """
    Compute a Unix timestamp (in seconds) for DynamoDB TTL expiration.

    parameters:
    - days: int – number of days from now to expire (default 14).

    returns:
    - int – future timestamp representing expiry time.
    """
    return int((datetime.utcnow() + timedelta(days=days)).timestamp())


def init_session(session_id: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Initialise a new session record in DynamoDB.

    parameters:
    - session_id: str – unique ID for the session (e.g. request or user identifier).
    - meta: dict (optional) – metadata such as 'created_by' or context details.

    returns:
    - dict – DynamoDB response from put_item().
    """
    item = {
        "session_id": session_id,
        "state": meta or {},
        "trace": [],
        "ttl_epoch": _ttl_epoch(),
    }
    return ddb.put_item(item)


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve an existing session record by its session_id.

    parameters:
    - session_id: str – ID of the session to retrieve.

    returns:
    - dict or None – session data if found, otherwise None.
    """
    return ddb.get_item(session_id)


def save_state(session_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Overwrite the 'state' field of a given session.

    parameters:
    - session_id: str – ID of the target session.
    - state: dict – new state to persist.

    returns:
    - dict – DynamoDB update response.
    """
    return ddb.update_json(session_id, "state", state)


def append_trace(session_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append an event record to a session’s 'trace' list.

    parameters:
    - session_id: str – ID of the session.
    - record: dict – structured event (e.g. {"event": "tool_call", "data": {...}}).

    returns:
    - dict – DynamoDB update response after adding the new trace entry.

    notes:
    - For high-volume or concurrent workloads, DynamoDB’s list_append operation
      would be more efficient. Here we use a simple fetch → append → update cycle
      for clarity and simplicity.
    """
    # Fetch existing session or create a default one if not found.
    sess = ddb.get_item(session_id) or {
        "session_id": session_id,
        "state": {},
        "trace": [],
        "ttl_epoch": _ttl_epoch()
    }

    # Append the new trace record.
    trace: List[Dict[str, Any]] = sess.get("trace", [])
    trace.append(record)

    # Save updated trace list back to DynamoDB.
    return ddb.update_json(session_id, "trace", trace)
