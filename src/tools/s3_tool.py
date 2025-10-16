import os, json, boto3
from typing import Any, Dict

s3 = boto3.client("s3")

def put_json(bucket: str, key: str, data: Dict[str, Any]) -> None:
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data).encode("utf-8"),
        ContentType="application/json"
    )
