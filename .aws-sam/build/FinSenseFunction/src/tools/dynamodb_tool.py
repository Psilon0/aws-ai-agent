from __future__ import annotations
import os
import json
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

_TABLE = os.getenv("DDB_SESSION_TABLE", "agent_sessions")
_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "eu-west-2"
_dynamodb = boto3.resource("dynamodb", region_name=_REGION)
_table = _dynamodb.Table(_TABLE)

def get_item(session_id: str) -> Optional[Dict[str, Any]]:
    try:
        res = _table.get_item(Key={"session_id": session_id})
        return res.get("Item")
    except ClientError as e:
        raise RuntimeError(f"DDB get_item failed: {e.response['Error']['Message']}")

def put_item(item: Dict[str, Any]) -> Dict[str, Any]:
    try:
        _table.put_item(Item=item)
        return {"ok": True}
    except ClientError as e:
        raise RuntimeError(f"DDB put_item failed: {e.response['Error']['Message']}")

def update_json(session_id: str, path: str, value: Any) -> Dict[str, Any]:
    """
    Update a top-level attribute safely. 'path' is an attribute name like 'state' or 'trace'.
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
