"""
Observability bootstrap:
- Structured logging is handled elsewhere.
- This enables AWS X-Ray subsegments and patches common libs when USE_XRAY=1.
- Safe no-op locally if not enabled or SDK not present.
"""
from __future__ import annotations
import os

def init_observability():
    use_xray = os.getenv("USE_XRAY", "0") == "1"
    if not use_xray:
        return None
    try:
        from aws_xray_sdk.core import xray_recorder, patch_all
        # Configure recorder; in Lambda the main segment is managed by the service
        xray_recorder.configure(service=os.getenv("XRAY_SERVICE_NAME", "FinSense"))
        # Patch common libraries. boto3 & requests are the big ones here.
        patch_all()  # patches: boto3, requests, sqlite3, etc.
        return xray_recorder
    except Exception:
        # Fail open: never break the app due to tracing
        return None

# Lightweight context manager helper for manual subsegments
class xray_segment:
    def __init__(self, name: str):
        self.name = name
        self.sub = None

    def __enter__(self):
        try:
            from aws_xray_sdk.core import xray_recorder
            self.sub = xray_recorder.begin_subsegment(self.name)
        except Exception:
            self.sub = None
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.sub is not None:
                from aws_xray_sdk.core import xray_recorder
                xray_recorder.end_subsegment()
        except Exception:
            pass
