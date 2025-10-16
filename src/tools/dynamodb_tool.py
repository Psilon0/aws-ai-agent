import boto3
from typing import Any, Dict

dynamodb = boto3.resource("dynamodb")

def put_item(table_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
    table = dynamodb.Table(table_name)
    return table.put_item(Item=item)
