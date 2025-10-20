from .types import Profile, MarketState, Bands, ModelOutput

class PortfolioModel:
    def recommend(self, profile: Profile, bands: Bands, market: MarketState, seed: int|None=None) -> ModelOutput:
        raise NotImplementedError
