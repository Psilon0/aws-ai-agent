from __future__ import annotations
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
import os
from src.tools import dynamodb_tool as ddb

DEFAULT_TTL_DAYS = int(os.getenv("SESSION_TTL_DAYS", "14"))

def _ttl_epoch(days: int = DEFAULT_TTL_DAYS) -> int:
    return int((datetime.utcnow() + timedelta(days=days)).timestamp())

def init_session(session_id: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    item = {
        "session_id": session_id,
        "state": meta or {},
        "trace": [],
        "ttl_epoch": _ttl_epoch(),
    }
    return ddb.put_item(item)

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return ddb.get_item(session_id)

def save_state(session_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    return ddb.update_json(session_id, "state", state)

def append_trace(session_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
    # Fetch, append, save (small & simple; for high volume you'd use list_append)
    sess = ddb.get_item(session_id) or {"session_id": session_id, "state": {}, "trace": [], "ttl_epoch": _ttl_epoch()}
    trace: List[Dict[str, Any]] = sess.get("trace", [])
    trace.append(record)
    return ddb.update_json(session_id, "trace", trace)
