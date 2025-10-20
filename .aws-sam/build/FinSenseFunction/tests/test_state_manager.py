import os
import boto3
from moto import mock_aws

os.environ["AWS_DEFAULT_REGION"] = os.environ.get("AWS_DEFAULT_REGION", "eu-west-2")
os.environ["DDB_SESSION_TABLE"] = "agent_sessions_test"

from src.tools import dynamodb_tool as ddb
from src import state_manager as sm

@mock_aws
def setup_table():
    ddbb = boto3.resource("dynamodb", region_name=os.environ["AWS_DEFAULT_REGION"])
    ddbb.create_table(
        TableName=os.environ["DDB_SESSION_TABLE"],
        AttributeDefinitions=[{"AttributeName": "session_id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "session_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )

@mock_aws
def test_session_lifecycle():
    setup_table()
    sid = "sess-123"
    assert sm.get_session(sid) is None
    sm.init_session(sid, {"user": "rafe"})
    s = sm.get_session(sid)
    assert s["session_id"] == sid
    sm.save_state(sid, {"step": 1})
    s2 = sm.get_session(sid)
    assert s2["state"]["step"] == 1
    sm.append_trace(sid, {"event": "x"})
    s3 = sm.get_session(sid)
    assert s3["trace"] and s3["trace"][-1]["event"] == "x"
