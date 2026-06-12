import logging

from src.schemas.analysis import MarketSnapshot

logger = logging.getLogger(__name__)


class MarketAgent:
    async def run(self, market: MarketSnapshot) -> list[str]:
        logger.info("Market reasoning started for %s", market.ticker)
        if market.day_change_percent is None:
            return ["Daily price movement is unavailable."]
        if market.day_change_percent > 1:
            return ["The stock is trading meaningfully higher versus the previous close."]
        if market.day_change_percent < -1:
            return ["The stock is trading meaningfully lower versus the previous close."]
        return ["The stock is trading near the previous close."]
