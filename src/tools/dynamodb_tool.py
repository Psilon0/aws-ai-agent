# PURPOSE: Helper functions to interact with DynamoDB for session storage.
# CONTEXT: Used by the FinSense agent to save, fetch, and update session data.
# CREDITS: Original work — no external code reuse.

from __future__ import annotations
import os
import json
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

# Get table name and region from environment, with safe defaults for local use.
_TABLE = os.getenv("DDB_SESSION_TABLE", "agent_sessions")
_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "eu-west-2"

# Connect to DynamoDB using boto3’s high-level resource API.
_dynamodb = boto3.resource("dynamodb", region_name=_REGION)
_table = _dynamodb.Table(_TABLE)

def get_item(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve one item (by session_id) from DynamoDB.

    parameters:
    - session_id: str – the unique ID used as the table's partition key.

    returns:
    - dict or None – the stored record, or None if not found.

    raises:
    - RuntimeError – if the DynamoDB request fails (wraps ClientError for readability).
    """
    try:
        res = _table.get_item(Key={"session_id": session_id})
        return res.get("Item")
    except ClientError as e:
        # Wrap the AWS error message in a simple RuntimeError for cleaner upstream handling.
        raise RuntimeError(f"DDB get_item failed: {e.response['Error']['Message']}")

def put_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert or replace a full record in DynamoDB.

    parameters:
    - item: dict – full object to store (must include 'session_id').

    returns:
    - dict – confirmation message {"ok": True} on success.

    raises:
    - RuntimeError – if DynamoDB put_item fails.
    """
    try:
        _table.put_item(Item=item)
        return {"ok": True}
    except ClientError as e:
        raise RuntimeError(f"DDB put_item failed: {e.response['Error']['Message']}")

def update_json(session_id: str, path: str, value: Any) -> Dict[str, Any]:
    """
    Update a single top-level attribute in a DynamoDB item.

    parameters:
    - session_id: str – which record to update.
    - path: str – top-level field name (e.g. 'state' or 'trace').
    - value: Any – the new value to set.

    returns:
    - dict – confirmation message {"ok": True} on success.

    raises:
    - RuntimeError – if the update fails (wraps boto3 ClientError).
    """
    try:
        _table.update_item(
            Key={"session_id": session_id},
            UpdateExpression=f"SET #k = :v",
            ExpressionAttributeNames={"#k": path},
            ExpressionAttributeValues={":v": value},
        )
        return {"ok": True}
    except ClientError as e:
        raise RuntimeError(f"DDB update_item failed: {e.response['Error']['Message']}")
