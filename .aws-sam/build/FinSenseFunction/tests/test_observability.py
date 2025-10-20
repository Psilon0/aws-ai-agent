import os
from src.observability import init_observability, xray_segment

def test_init_observability_noop_by_default(monkeypatch):
    monkeypatch.delenv("USE_XRAY", raising=False)  # default off
    rec = init_observability()
    assert rec is None  # should be safe no-op

def test_xray_segment_ctx_noop_without_recorder():
    # Even if X-Ray isn't enabled, context manager should not raise
    with xray_segment("fake-segment"):
        pass

def test_init_observability_on(monkeypatch):
    # Enabling should not raise; may still return None locally if SDK misconfigured
    monkeypatch.setenv("USE_XRAY", "1")
    rec = init_observability()
    # We can't assert recorder truthiness in every environment, but it should not explode
    assert rec is None or hasattr(rec, "begin_subsegment")
