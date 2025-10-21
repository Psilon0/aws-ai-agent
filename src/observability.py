"""
Observability bootstrap.

PURPOSE:
- Optionally enables AWS X-Ray distributed tracing when USE_XRAY=1.
- Adds automatic instrumentation for common libraries (e.g. boto3, requests).
- Safely degrades to a no-op if X-Ray is not enabled or the SDK is unavailable.

CONTEXT:
- Used within FinSense Lambda or local environments where tracing may or may not be active.
- Logging is configured separately in logging_setup.py.

CREDITS:
- Original work — no external code reuse.
NOTE:
- Behaviour unchanged; comments/docstrings only.
"""
from __future__ import annotations
import os


def init_observability():
    """
    Optionally initialise AWS X-Ray instrumentation.

    returns:
    - xray_recorder object if successfully configured.
    - None if X-Ray is disabled or not available.

    flow:
    1) Check USE_XRAY environment variable (default = off).
    2) If enabled, import AWS X-Ray SDK and patch common libraries.
    3) Fail silently if SDK import or setup fails — never break execution.

    notes:
    - In AWS Lambda, the main segment is automatically managed by AWS.
    - patch_all() instruments boto3, requests, and other supported libraries.
    """
    use_xray = os.getenv("USE_XRAY", "0") == "1"
    if not use_xray:
        return None
    try:
        from aws_xray_sdk.core import xray_recorder, patch_all
        # Configure the X-Ray recorder; sets the service name for tracing.
        xray_recorder.configure(service=os.getenv("XRAY_SERVICE_NAME", "FinSense"))
        # Automatically patch common libraries for trace propagation.
        patch_all()  # patches: boto3, requests, sqlite3, etc.
        return xray_recorder
    except Exception:
        # Fail open: tracing should never block or crash the application.
        return None


class xray_segment:
    """
    Lightweight context manager for manual subsegments.

    usage example:
    >>> with xray_segment("run_pipeline"):
    >>>     result = run_pipeline(payload)

    behaviour:
    - Begins an X-Ray subsegment on entry.
    - Closes it automatically on exit, even if an error occurs.
    - Silently ignores all exceptions to ensure safety when tracing is unavailable.
    """

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
            # Suppress all errors to keep tracing optional and non-blocking.
            pass
