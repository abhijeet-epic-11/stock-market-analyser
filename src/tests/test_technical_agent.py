import asyncio
from datetime import datetime, timedelta
import unittest

from src.agents.technical_agent import TechnicalAgent
from src.schemas.analysis import MarketSnapshot, PriceBar


class TechnicalAgentTest(unittest.TestCase):
    def test_technical_agent_scores_uptrend(self) -> None:
        start = datetime(2026, 1, 1)
        bars = [
            PriceBar(
                date=start + timedelta(days=index),
                open=100 + index,
                high=102 + index,
                low=99 + index,
                close=100 + index,
                volume=1000 + index,
            )
            for index in range(60)
        ]
        market = MarketSnapshot(ticker="TEST", price=159, volume=1059, history=bars)

        technical = asyncio.run(TechnicalAgent().run(market))

        self.assertGreaterEqual(technical.score, 65)
        self.assertEqual(technical.trend, "bullish")
        self.assertIn("Price is above 50 DMA", technical.bullish_factors)


if __name__ == "__main__":
    unittest.main()
