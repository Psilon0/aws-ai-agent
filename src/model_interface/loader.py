import importlib, os
from .portfolio_model import PortfolioModel

def load_model() -> PortfolioModel:
    modpath = os.getenv("MODEL_MODULE")
    if not modpath:
        from src.model_impl.stub_model import StubModel
        return StubModel()
    mod, factory = modpath.split(":")
    return getattr(importlib.import_module(mod), factory)()
