from __future__ import annotations
from src.pipeline import run_pipeline

class Agent:
    def handle(self, payload: dict) -> dict:
        return run_pipeline(payload)
